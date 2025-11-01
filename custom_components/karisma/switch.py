"""Platform for Karisma switch."""

import functools
import logging

import voluptuous as vol

from . import async_get_or_create
from homeassistant.components.switch import PLATFORM_SCHEMA, ToggleEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_FLOW_PIN_NAME,
    CONF_FLOW_PIN_NUMBER,
    CONF_FLOW_PLATFORM,
    CONF_I2C_ADDRESS,
    CONF_PINS,
    DEFAULT_I2C_ADDRESS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_SWITCHES_SCHEMA = vol.Schema({cv.positive_int: cv.string})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PINS): _SWITCHES_SCHEMA,
        vol.Optional(CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS): vol.Coerce(int),
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Karisma for switch entities."""
    for pin_number, pin_name in config[CONF_PINS].items():
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_FLOW_PLATFORM: "switch",
                    CONF_FLOW_PIN_NUMBER: pin_number,
                    CONF_FLOW_PIN_NAME: pin_name,
                    CONF_I2C_ADDRESS: config[CONF_I2C_ADDRESS],
                },
            )
        )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a Karisma switch entry."""
    switch_entity = KARISMASwitch(config_entry)
    switch_entity.device = await async_get_or_create(
        hass, config_entry, switch_entity
    )

    # if await hass.async_add_executor_job(switch_entity.configure_device):
    async_add_entities([switch_entity])


async def async_unload_entry(hass, config_entry):
    """Unload Karisma switch entry corresponding to config_entry."""
    _LOGGER.warning("[FIXME] async_unload_entry not implemented")


class KARISMASwitch(ToggleEntity):
    """Represent a switch that uses Karisma."""

    def __init__(self, config_entry):
        """Initialize the Karisma switch."""
        self._device = None
        self._state = False

        self._i2c_address = config_entry.data[CONF_I2C_ADDRESS]
        self._pin_name = config_entry.data[CONF_FLOW_PIN_NAME]
        self._pin_number = config_entry.data[CONF_FLOW_PIN_NUMBER]

        # Subscribe to updates of config entry options
        self._unsubscribe_update_listener = config_entry.add_update_listener(
            self.async_config_update
        )

        _LOGGER.info(
            "%s(pin %d:'%s') created",
            type(self).__name__,
            self._pin_number,
            self._pin_name,
        )

    @property
    def icon(self):
        """Return device icon for this entity."""
        return "mdi:lightning-bolt-circle"

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._device.unique_id}-{self._pin_number}"

    @property
    def name(self):
        """Return the name of the switch."""
        return self._pin_name

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def pin(self):
        """Return the pin number of the entity."""
        return self._pin_number

    @property
    def address(self):
        """Return the i2c address of the entity."""
        return self._i2c_address

    @property
    def device_info(self):
        """Device info."""
        return {
            "identifiers": {(DOMAIN, self._i2c_address)},
            "manufacturer": "Karisma",
            "model": "Relay",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def device(self):
        """Get device property."""
        return self._device

    @device.setter
    def device(self, value):
        """Set device property."""
        self._device = value

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        await self.hass.async_add_executor_job(
            functools.partial(
                self._device.set_pin_value, self._pin_number, True
            )
        )
        self._state = True
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        await self.hass.async_add_executor_job(
            functools.partial(
                self._device.set_pin_value, self._pin_number, False
            )
        )
        self._state = False
        self.schedule_update_ha_state()

    @callback
    async def async_config_update(self, hass, config_entry):
        """Handle update from config entry options."""
        await hass.async_add_executor_job(
            functools.partial(
                self._device.set_pin_value,
                self._pin_number,
                self._state,
            )
        )
        self.async_schedule_update_ha_state()

    def unsubscribe_update_listener(self):
        """Remove listener from config entry options."""
        self._unsubscribe_update_listener()

