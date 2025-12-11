from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict

_LOGGER = logging.getLogger(__name__)


class FelicityApiError(Exception):
    """Error while communicating with Felicity battery."""


class FelicityClient:
    """Async TCP client for Felicity local monitor protocol."""

    def __init__(self, host: str, port: int, timeout: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout

    async def _async_read_raw(self, payload: bytes) -> str:
        """Send raw bytes and read reply as string."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=self._timeout
            )
        except Exception as err:
            raise FelicityApiError(f"Failed to connect to {self._host}:{self._port}") from err

        try:
            writer.write(payload)
            await writer.drain()
            data = await asyncio.wait_for(reader.read(64 * 1024), timeout=self._timeout)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
        except Exception as err:
            raise FelicityApiError("Error during TCP read/write") from err

        text = data.decode(errors="ignore")
        _LOGGER.debug("Raw Felicity response: %r", text)
        return text

    async def async_get_data(self) -> Dict[str, Any]:
        """Fetch and combine runtime, basic and settings data into one dict.

        Uses three commands:
        - wifilocalMonitor:get dev real infor   -> runtime values (Batt, Batsoc, temps, etc.)
        - wifilocalMonitor:get dev basice infor -> versions / type
        - wifilocalMonitor:get dev set infor    -> config / limits (multi-json)
        """
        # 1. Runtime data
        real_raw = await self._async_read_raw(b"wifilocalMonitor:get dev real infor")
        real = self._parse_real_payload(real_raw)
        data: Dict[str, Any] = dict(real)

        # 2. Basic info
        try:
            basic_raw = await self._async_read_raw(
                b"wifilocalMonitor:get dev basice infor"
            )
            basic_text = basic_raw.replace("'", '"').strip()
            basic = json.loads(basic_text)
            data["_basic"] = basic
        except Exception as err:
            _LOGGER.debug("Failed to read basic info: %s", err)

        # 3. Settings / limits (может быть в нескольких JSON-блоках)
        try:
            set_raw = await self._async_read_raw(
                b"wifilocalMonitor:get dev set infor"
            )
            set_text = set_raw.replace("'", '"').strip()
            merged: Dict[str, Any] = {}

            # Разбираем несколько JSON-объектов подряд:
            depth = 0
            buf = []
            for ch in set_text:
                buf.append(ch)
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        chunk = "".join(buf).strip()
                        buf = []
                        try:
                            obj = json.loads(chunk)
                            if isinstance(obj, dict):
                                merged.update(obj)
                        except Exception:
                            _LOGGER.debug("Failed to parse settings chunk: %r", chunk)

            if merged:
                data["_settings"] = merged
                _LOGGER.debug(
                    "Merged Felicity settings (%d keys): %s",
                    len(merged),
                    merged,
                )
            else:
                _LOGGER.debug("No valid JSON found in settings payload: %r", set_text)

        except Exception as err:
            _LOGGER.debug("Failed to read settings info: %s", err)

        return data

    # -------------------------------------------------------------------------
    # Parsing helpers
    # -------------------------------------------------------------------------

    def _parse_real_payload(self, text: str) -> Dict[str, Any]:
        """Parse Felicity 'dev real infor' payload into dict we use."""
        norm = text.replace("'", '"')
        last_brace = norm.rfind("}")
        if last_brace != -1:
            norm = norm[: last_brace + 1]

        result: Dict[str, Any] = {}

        # Сначала пытаемся распарсить полный JSON так, как его отдаёт устройство.
        # Это позволяет сохранить все верхнеуровневые поля (ACin/ACout/PV/Energy/busVp/workM/fault/warn/lPerc/etc.)
        try:
            full = json.loads(norm)
            if isinstance(full, dict):
                result.update(full)
        except Exception:
            _LOGGER.debug("Failed to parse full JSON from real payload: %r", text)

        def _find_str(key: str) -> str | None:
            m = re.search(rf'"{key}"\s*:\s*"([^"]*)"', norm)
            return m.group(1) if m else None

        def _find_int(key: str) -> int | None:
            m = re.search(rf'"{key}"\s*:\s*([-0-9]+)', norm)
            return int(m.group(1)) if m else None

        # Simple fields
        result["CommVer"] = _find_int("CommVer")
        dev_sn = _find_str("DevSN")
        wifi_sn = _find_str("wifiSN")
        if dev_sn:
            result["DevSN"] = dev_sn
        if wifi_sn:
            result["wifiSN"] = wifi_sn

        # Numeric 'Bfault' and 'Bwarn'
        bfault = _find_int("Bfault")
        bwarn = _find_int("Bwarn")
        if bfault is not None:
            result["Bfault"] = bfault
        if bwarn is not None:
            result["Bwarn"] = bwarn

        # Batt: [[52100],[-112],[-604,-480]]
        m = re.search(
            r'"Batt"\s*:\s*\[\s*\[\s*([-0-9]+)\s*\]\s*,\s*\[\s*([-0-9]+)\s*\]\s*,\s*\[\s*([-0-9]+)\s*,\s*([-0-9]+)\s*\]\s*\]',
            norm,
        )
        if m:
            v = int(m.group(1))
            i = int(m.group(2))
            p_chg = int(m.group(3))
            p_dis = int(m.group(4))
            result["Batt"] = [[v], [i], [p_chg, p_dis]]

        # Batsoc: [[8400,0,0]]
        m = re.search(
            r'"Batsoc"\s*:\s*\[\s*\[\s*([-0-9]+)\s*,\s*([-0-9]+)\s*,\s*([-0-9]+)\s*\]\s*\]',
            norm,
        )
        if m:
            soc = int(m.group(1))
            scale = int(m.group(2))
            cap = int(m.group(3))
            result["Batsoc"] = [[soc, scale, cap]]

        # BMaxMin: [[3345,3338],[6,7]]
        m = re.search(
            r'"BMaxMin"\s*:\s*\[\s*\[\s*([-0-9]+)\s*,\s*([-0-9]+)\s*\]\s*,\s*\[\s*([-0-9]+)\s*,\s*([-0-9]+)\s*\]\s*\]',
            norm,
        )
        if m:
            max_v = int(m.group(1))
            min_v = int(m.group(2))
            max_i = int(m.group(3))
            min_i = int(m.group(4))
            result["BMaxMin"] = [[max_v, min_v], [max_i, min_i]]

        # LVolCur: [[576,480],[100,1500]]
        m = re.search(
            r'"LVolCur"\s*:\s*\[\s*\[\s*([-0-9]+)\s*,\s*([-0-9]+)\s*\]\s*,\s*\[\s*([-0-9]+)\s*,\s*([-0-9]+)\s*\]\s*\]',
            norm,
        )
        if m:
            v1 = int(m.group(1))
            v2 = int(m.group(2))
            c1 = int(m.group(3))
            c2 = int(m.group(4))
            result["LVolCur"] = [[v1, v2], [c1, c2]]

        # BTemp: [[320,0,234,233,226,0,0,0]]
        m = re.search(
            r'"BTemp"\s*:\s*\[\s*\[\s*([-0-9,\s]+)\s*\]\s*\]', norm
        )
        if m:
            temps_str = m.group(1)
            try:
                temps = [int(x) for x in temps_str.split(",") if x.strip() != ""]
                result["BTemp"] = [temps]
            except Exception:
                _LOGGER.debug("Failed to parse BTemp from %r", temps_str)

        # BatcelList
        m = re.search(r'"BatcelList"\s*:\s*\[\s*\[([0-9,\s-]+)\]', norm)
        if m:
            cells_str = m.group(1)
            try:
                cells = [int(x) for x in cells_str.split(",") if x.strip() != ""]
                result["BatcelList"] = [cells]
            except Exception:
                _LOGGER.debug("Failed to parse BatcelList from %r", cells_str)

        # BatInOut: [103,0] - мощность / направление
        m = re.search(
            r'"BatInOut"\s*:\s*\[\s*([-0-9]+)\s*,\s*([-0-9]+)\s*\]', norm
        )
        if m:
            p = int(m.group(1))
            flag = int(m.group(2))
            result["BatInOut"] = [p, flag]

        _LOGGER.debug("Parsed Felicity real data dict: %s", result)

        # Минимальная проверка: должны быть основные поля Batsoc или Batt
        if "Batsoc" not in result and "Batt" not in result:
            raise FelicityApiError(
                f"Unable to parse essential fields from payload: {text}"
            )

        return result
