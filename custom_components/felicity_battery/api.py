from __future__ import annotations

import asyncio
import json
import logging

_LOGGER = logging.getLogger(__name__)


class FelicityApiError(Exception):
    """Error while communicating with Felicity battery."""


class FelicityClient:
    """TCP client for Felicity battery local API."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    async def async_get_data(self) -> dict:
        """Send command and get JSON response."""
        try:
            reader, writer = await asyncio.open_connection(self._host, self._port)

            # Same command as used via printf | nc
            writer.write(b"wifilocalMonitor:get dev real infor")
            await writer.drain()

            try:
                data = await asyncio.wait_for(reader.read(4096), timeout=3.0)
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

        except Exception as err:
            raise FelicityApiError(
                f"Error talking to {self._host}:{self._port}: {err}"
            ) from err

        if not data:
            raise FelicityApiError("No data received from battery")

        text = data.decode("ascii", errors="ignore").strip()
        _LOGGER.debug("Raw Felicity response: %r", text)

        try:
            parsed = json.loads(text)
        except Exception as err:
            raise FelicityApiError(f"Invalid JSON from battery: {text!r}") from err

        return parsed
