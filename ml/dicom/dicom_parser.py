"""
========================================================================================
VisionCare AI: Module 7 — Native Clinical DICOM Ingestion Engine
========================================================================================
Purpose: Ingests raw Part 10 Medical DICOM (.dcm) frontal radiographs.
Features:
  - Automatic Photometric Interpretation correction (MONOCHROME1 -> MONOCHROME2)
  - VOI LUT Window/Level decoding ((0028,1050) Center / (0028,1051) Width)
  - Physical millimeter pixel spacing extraction ((0028,0030) Pixel Spacing)
  - Patient demographics tag decoding (Patient ID, Age, Gender, View PA/AP)
  - Seamless fallback pure-Python parser if pydicom is not pre-installed
========================================================================================
"""

import io
import re
import struct
from typing import Dict, Any, Tuple, Optional, Union
import numpy as np
import cv2


class DICOMParser:
    """
    Robust DICOM Parser supporting pydicom with pure-Python Part 10 fallback.
    """

    @staticmethod
    def is_dicom_bytes(data: bytes) -> bool:
        """Determines if raw byte stream has the standard DICOM Part 10 signature."""
        if len(data) > 132 and data[128:132] == b"DICM":
            return True
        # Alternate DICOM without preamble (starts directly with Group 0008)
        if len(data) > 8 and data[:2] in (b"\x08\x00", b"\x00\x08"):
            return True
        return False

    @staticmethod
    def parse(data: bytes) -> Dict[str, Any]:
        """
        Parses raw DICOM bytes into an 8-bit diagnostic numpy image array
        and clinical metadata dictionary.
        """
        # Try pydicom if available
        try:
            import pydicom
            return DICOMParser._parse_with_pydicom(data)
        except ImportError:
            return DICOMParser._parse_pure_python(data)

    @staticmethod
    def _parse_with_pydicom(data: bytes) -> Dict[str, Any]:
        import pydicom
        from pydicom.pixel_data_handlers.util import apply_voi_lut

        ds = pydicom.dcmread(io.BytesIO(data), force=True)

        # 1. Extract demographics
        patient_id = str(getattr(ds, "PatientID", "ANONYMOUS"))
        
        # Age
        age = 55
        age_str = str(getattr(ds, "PatientAge", ""))
        match = re.search(r"\d+", age_str)
        if match:
            age = int(match.group())

        # Gender
        gender = str(getattr(ds, "PatientSex", "M")).upper()
        if gender not in ("M", "F", "O"):
            gender = "M"

        # View Position
        view_pos = str(getattr(ds, "ViewPosition", "PA")).upper()
        if "AP" in view_pos:
            view_pos = "AP"
        else:
            view_pos = "PA"

        # Pixel Spacing (mm)
        pixel_spacing = (0.143, 0.143)
        if hasattr(ds, "PixelSpacing") and len(ds.PixelSpacing) >= 2:
            pixel_spacing = (float(ds.PixelSpacing[0]), float(ds.PixelSpacing[1]))
        elif hasattr(ds, "ImagerPixelSpacing") and len(ds.ImagerPixelSpacing) >= 2:
            pixel_spacing = (float(ds.ImagerPixelSpacing[0]), float(ds.ImagerPixelSpacing[1]))

        # Photometric Interpretation
        photo_interp = str(getattr(ds, "PhotometricInterpretation", "MONOCHROME2")).strip()

        # Window/Level
        wc = getattr(ds, "WindowCenter", None)
        ww = getattr(ds, "WindowWidth", None)
        if isinstance(wc, (list, pydicom.multival.MultiValue)):
            wc = float(wc[0])
        elif wc is not None:
            wc = float(wc)

        if isinstance(ww, (list, pydicom.multival.MultiValue)):
            ww = float(ww[0])
        elif ww is not None:
            ww = float(ww)

        # 2. Extract & calibrate Pixel Array
        try:
            arr = ds.pixel_array.astype(np.float32)
        except Exception:
            arr = np.zeros((512, 512), dtype=np.float32)

        # Rescale Slope & Intercept
        slope = float(getattr(ds, "RescaleSlope", 1.0))
        intercept = float(getattr(ds, "RescaleIntercept", 0.0))
        if slope != 1.0 or intercept != 0.0:
            arr = arr * slope + intercept

        # Apply Window/Level VOI LUT if present
        if wc is not None and ww is not None and ww > 0:
            img_min = wc - ww / 2.0
            img_max = wc + ww / 2.0
            arr = np.clip(arr, img_min, img_max)
            arr = (arr - img_min) / (img_max - img_min) * 255.0
        else:
            p_min, p_max = arr.min(), arr.max()
            if p_max > p_min:
                arr = (arr - p_min) / (p_max - p_min) * 255.0
            else:
                arr = np.zeros_like(arr)

        img_uint8 = np.clip(arr, 0, 255).astype(np.uint8)

        # Invert MONOCHROME1 to standard MONOCHROME2 (so air is dark and bone is white)
        if photo_interp == "MONOCHROME1":
            img_uint8 = 255 - img_uint8

        return {
            "image": img_uint8,
            "patient_id": patient_id,
            "age": age,
            "gender": gender,
            "view_position": view_pos,
            "pixel_spacing": pixel_spacing,
            "photometric_interpretation": photo_interp,
            "window_center": wc,
            "window_width": ww,
            "modality": str(getattr(ds, "Modality", "DX")),
            "is_dicom": True
        }

    @staticmethod
    def _parse_pure_python(data: bytes) -> Dict[str, Any]:
        """
        Pure Python Part 10 parser for uncompressed explicit/implicit VR DICOM files.
        """
        # Default fallback metadata
        patient_id = "ANONYMOUS-DCM"
        age = 55
        gender = "M"
        view_pos = "PA"
        pixel_spacing = (0.143, 0.143)
        photo_interp = "MONOCHROME2"
        wc, ww = None, None
        rows, cols = 512, 512
        bits_allocated = 16
        pixel_data_bytes = None

        offset = 132 if (len(data) > 132 and data[128:132] == b"DICM") else 0
        total_len = len(data)

        # Standard DICOM Tag Dictionary (Tag -> Attribute Name)
        tag_handlers = {
            (0x0010, 0x0020): "patient_id",
            (0x0010, 0x0040): "gender",
            (0x0010, 0x1010): "age",
            (0x0018, 0x5101): "view_position",
            (0x0028, 0x0004): "photo_interp",
            (0x0028, 0x0010): "rows",
            (0x0028, 0x0011): "cols",
            (0x0028, 0x0030): "pixel_spacing",
            (0x0028, 0x0100): "bits_allocated",
            (0x0028, 0x1050): "window_center",
            (0x0028, 0x1051): "window_width",
            (0x7FE0, 0x0010): "pixel_data",
        }

        while offset + 8 <= total_len:
            group, element = struct.unpack("<HH", data[offset:offset+4])
            tag = (group, element)
            offset += 4

            if offset >= total_len:
                break

            # Check if explicit VR (2 ASCII uppercase letters)
            vr = data[offset:offset+2]
            is_explicit = (
                vr.isalpha() and vr.isupper() and len(vr) == 2
                and chr(vr[0]) in "AUBDCSFOILNPSTU"
            )

            if is_explicit:
                offset += 2
                if vr in (b"OB", b"OW", b"OF", b"SQ", b"UT", b"UN"):
                    offset += 2  # Reserved 2 bytes
                    if offset + 4 > total_len:
                        break
                    vl = struct.unpack("<I", data[offset:offset+4])[0]
                    offset += 4
                else:
                    if offset + 2 > total_len:
                        break
                    vl = struct.unpack("<H", data[offset:offset+2])[0]
                    offset += 2
            else:
                # Implicit VR: 4-byte VL
                if offset + 4 > total_len:
                    break
                vl = struct.unpack("<I", data[offset:offset+4])[0]
                offset += 4

            # Undefined length handling (e.g. encapsulated pixel data 0xFFFFFFFF)
            if vl == 0xFFFFFFFF:
                vl = total_len - offset

            if offset + vl > total_len:
                vl = total_len - offset

            val_bytes = data[offset:offset+vl]
            offset += vl

            # Handle recognized tags
            name = tag_handlers.get(tag)
            if name == "patient_id":
                try: patient_id = val_bytes.decode("ascii", errors="ignore").strip()
                except Exception: pass
            elif name == "gender":
                try:
                    g = val_bytes.decode("ascii", errors="ignore").strip().upper()
                    if g in ("M", "F"): gender = g
                except Exception: pass
            elif name == "age":
                try:
                    match = re.search(r"\d+", val_bytes.decode("ascii", errors="ignore"))
                    if match: age = int(match.group())
                except Exception: pass
            elif name == "view_position":
                try:
                    v = val_bytes.decode("ascii", errors="ignore").strip().upper()
                    view_pos = "AP" if "AP" in v else "PA"
                except Exception: pass
            elif name == "photo_interp":
                try: photo_interp = val_bytes.decode("ascii", errors="ignore").strip()
                except Exception: pass
            elif name == "rows":
                try: rows = struct.unpack("<H", val_bytes[:2])[0]
                except Exception: pass
            elif name == "cols":
                try: cols = struct.unpack("<H", val_bytes[:2])[0]
                except Exception: pass
            elif name == "bits_allocated":
                try: bits_allocated = struct.unpack("<H", val_bytes[:2])[0]
                except Exception: pass
            elif name == "window_center":
                try: wc = float(val_bytes.decode("ascii", errors="ignore").strip().split("\\")[0])
                except Exception: pass
            elif name == "window_width":
                try: ww = float(val_bytes.decode("ascii", errors="ignore").strip().split("\\")[0])
                except Exception: pass
            elif name == "pixel_spacing":
                try:
                    sp = val_bytes.decode("ascii", errors="ignore").strip().split("\\")
                    if len(sp) >= 2:
                        pixel_spacing = (float(sp[0]), float(sp[1]))
                except Exception: pass
            elif name == "pixel_data":
                pixel_data_bytes = val_bytes
                break

        # Decode pixel array
        if pixel_data_bytes is not None and len(pixel_data_bytes) > 0:
            dtype = np.uint16 if bits_allocated == 16 else np.uint8
            needed_bytes = rows * cols * (2 if bits_allocated == 16 else 1)
            raw_slice = pixel_data_bytes[:needed_bytes]

            try:
                arr = np.frombuffer(raw_slice, dtype=dtype)
                if len(arr) == rows * cols:
                    arr = arr.reshape((rows, cols)).astype(np.float32)
                else:
                    arr = np.zeros((rows, cols), dtype=np.float32)
            except Exception:
                arr = np.zeros((rows, cols), dtype=np.float32)
        else:
            arr = np.zeros((rows, cols), dtype=np.float32)

        # Window/Level contrast normalization
        if wc is not None and ww is not None and ww > 0:
            img_min = wc - ww / 2.0
            img_max = wc + ww / 2.0
            arr = np.clip(arr, img_min, img_max)
            arr = (arr - img_min) / (img_max - img_min) * 255.0
        else:
            p_min, p_max = arr.min(), arr.max()
            if p_max > p_min:
                arr = (arr - p_min) / (p_max - p_min) * 255.0
            else:
                arr = np.zeros_like(arr)

        img_uint8 = np.clip(arr, 0, 255).astype(np.uint8)

        # Invert MONOCHROME1
        if photo_interp == "MONOCHROME1":
            img_uint8 = 255 - img_uint8

        return {
            "image": img_uint8,
            "patient_id": patient_id,
            "age": age,
            "gender": gender,
            "view_position": view_pos,
            "pixel_spacing": pixel_spacing,
            "photometric_interpretation": photo_interp,
            "window_center": wc,
            "window_width": ww,
            "modality": "DX",
            "is_dicom": True
        }
