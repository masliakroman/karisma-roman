"""Support for I2C KARISMA Relay."""

import asyncio
import functools
import logging

import smbus2

from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import device_registry

from .const import (
    CONF_FLOW_PLATFORM,
    CONF_I2C_ADDRESS,
    DOMAIN,
)


# # Register address used to toggle IOCON.BANK to 1 (only mapped when BANK is 0)
# IOCON_REMAP = 0x0b

_LOGGER = logging.getLogger(__name__)

DATA_LOCK = asyncio.Lock()


async def async_setup(hass, config):
    """Set up the component."""

    # hass.data[DOMAIN] stores one entry for each Karisma instance using i2c address as a key
    hass.data.setdefault(DOMAIN, {})

    # Callback function to start polling when HA starts
    def start_polling(event):
        for component in hass.data[DOMAIN].values():
            if not component.is_alive():
                component.start_polling()

    # Callback function to stop polling when HA stops
    def stop_polling(event):
        for component in hass.data[DOMAIN].values():
            if component.is_alive():
                component.stop_polling()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, start_polling)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_polling)

    return True


async def async_setup_entry(hass, config_entry):
    """Set up the Karisma from a config entry."""

    # Forward entry setup to configured platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(
            config_entry, config_entry.data[CONF_FLOW_PLATFORM]
        )
    )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload entity from Karisma component and platform."""

    # Unload related platform
    await hass.config_entries.async_forward_entry_unload(
        config_entry, config_entry.data[CONF_FLOW_PLATFORM]
    )

    i2c_address = config_entry.data[CONF_I2C_ADDRESS]

    # DOMAIN data async mutex
    async with DATA_LOCK:
        if i2c_address in hass.data[DOMAIN]:
            component = hass.data[DOMAIN][i2c_address]

            await hass.async_add_executor_job(component.stop_polling)
            hass.data[DOMAIN].pop(i2c_address)

    return True


async def async_get_or_create(hass, config_entry, entity):
    """Get or create a Karisma component from entity i2c address."""

    i2c_address = entity.address

    # DOMAIN data async mutex
    try:
        async with DATA_LOCK:
            if i2c_address in hass.data[DOMAIN]:
                component = hass.data[DOMAIN][i2c_address]
            else:
                # Try to create component when it doesn't exist
                component = await hass.async_add_executor_job(
                    functools.partial(KARISMA, i2c_address)
                )
                hass.data[DOMAIN][i2c_address] = component

                # Start polling thread if hass is already running
                if hass.is_running:
                    component.start_polling()

                # Register a device combining all related entities
                devices = device_registry.async_get(hass)
                devices.async_get_or_create(
                    config_entry_id=config_entry.entry_id,
                    identifiers={(DOMAIN, i2c_address)},
                    manufacturer="Karisma",
                    model=DOMAIN,
                    name=f"{DOMAIN}@0x{i2c_address:02x}",
                )

    except ValueError as error:
        component = None
        await hass.config_entries.async_remove(config_entry.entry_id)

        hass.components.persistent_notification.create(
            f"Error: Unable to access {DOMAIN}-0x{i2c_address:02x} ({error})",
            title=f"{DOMAIN} Configuration",
            notification_id=f"{DOMAIN} notification",
        )

    return component


class KARISMA:
    """KARISMA device driver."""

    def __init__(self, address):
        """Create a KARISMA instance at {address} on I2C {bus}."""
        self._address = address
        self._bus = None

        self._run = False

    @property
    def unique_id(self):
        """Return component unique id."""
        return f"{DOMAIN}-0x{self._address:02x}"

    def set_pin_value(self, pin, value):
        """Set KARISMA GPIO[{pin}] to {value}."""
        if self._bus is not None:
            data = (100 + pin) if value else pin
            self._bus.write_byte_data(self._address, 0, data)
        else:
            _LOGGER.error("Bus in None")


    def is_alive(self):
        return self._run

    def start_polling(self):
        """Start polling thread."""
        try:
            self._bus = smbus2.SMBus(1)
            self._bus.read_byte(self._address)
            self._bus.write_byte_data(self._address, 0, 200)
        except (FileNotFoundError, OSError) as error:
            _LOGGER.error(
                "Unable to access %s (%s)",
                self.unique_id,
                error,
            )
            raise ValueError(error) from error

        self._run = True

    def stop_polling(self):
        self._bus = None
        """Stop polling thread."""
        self._run = False


