"""Config flow for KARISMA component."""

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.config_entries import SOURCE_IMPORT


import logging

from .const import (
    CONF_FLOW_PIN_NAME,
    CONF_FLOW_PIN_NUMBER,
    CONF_FLOW_PLATFORM,
    CONF_I2C_ADDRESS,
    CONF_FLOW_ADDR,
    CONF_FLOW_ADDR_A,
    CONF_FLOW_ADDR_B,
    CONF_FLOW_ADDR_C,
    CONF_FLOW_ADDR_D,
    CONF_FLOW_ADDR_E,
    CONF_FLOW_ADDR_F,
    FORM_PIN_NAME_,
    DOMAIN,
)

RELAY_TYPES = ["16 ports"]

_LOGGER = logging.getLogger(__name__)

class KarismaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Karisma config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def _value_or_empty(self, user_input, key):
        return user_input[key] if key in user_input else ""

    def _addr_dic_to_title(self, addr_dic):
        res = ""
        if CONF_FLOW_ADDR_A in addr_dic:
            res += "A"
        if CONF_FLOW_ADDR_B in addr_dic:
            res += "B"
        if CONF_FLOW_ADDR_C in addr_dic:
            res += "C"
        if CONF_FLOW_ADDR_D in addr_dic:
            res += "D"
        if CONF_FLOW_ADDR_E in addr_dic:
            res += "E"
        if CONF_FLOW_ADDR_F in addr_dic:
            res += "F"
        if res == "":
            return "N"
        return res


    def _unique_id(self, user_input):
        return "%s.%d.%d" % (
            DOMAIN,
            user_input[CONF_I2C_ADDRESS],
            user_input[CONF_FLOW_PIN_NUMBER],
        )



    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     """Add support for config flow options."""
    #     return KarismaOptionsFlowHandler(config_entry)

    async def async_step_import(self, user_input=None):
        """Create a new entity from configuration.yaml import."""
        config_entry = await self.async_set_unique_id(self._unique_id(user_input))
        # Remove entry (from storage) matching the same unique id
        if config_entry:
            self.hass.config_entries.async_remove(config_entry.entry_id)

        return self.async_create_entry(
            title=user_input[CONF_FLOW_PIN_NAME],
            data=user_input,
        )


    async def async_step_user(self, user_input=None):
        """Create a new entity from UI."""

        if user_input is not None:
            # Add devices
            return await self._add_entities(user_input)

        addr_dict = {
            CONF_FLOW_ADDR_A: "A",
            CONF_FLOW_ADDR_B: "B",
            CONF_FLOW_ADDR_C: "C",
            CONF_FLOW_ADDR_D: "D",
            CONF_FLOW_ADDR_E: "E",
            CONF_FLOW_ADDR_F: "F"
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FLOW_ADDR, default=[]): cv.multi_select(
                        addr_dict
                    ),
                    # vol.Required(CONF_FLOW_PIN_NUMBER, default=0): vol.All(
                    #     vol.Coerce(int), vol.Range(min=0, max=15)
                    # ),
                    # vol.Required(
                    #     CONF_FLOW_PLATFORM,
                    #     default=PLATFORMS[0],
                    # ): vol.In(PLATFORMS),
                    vol.Required(
                        "relay_type",
                        default=RELAY_TYPES[0],
                    ): vol.In(RELAY_TYPES),

                    vol.Optional(FORM_PIN_NAME_+str(0), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(1), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(2), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(3), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(4), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(5), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(6), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(7), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(8), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(9), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(10), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(11), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(12), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(13), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(14), default=""): str,
                    vol.Optional(FORM_PIN_NAME_+str(15), default=""): str,
                }
            ),
        )

    async def _add_entities(self, user_input):

        for pin_number in range(0, 15):  # iterates till 14 because the 15th goes next after this
            data_entity = self._map_data_entity_from_user_input(user_input, pin_number)
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_IMPORT},
                    data=data_entity,
                )
            )

        data_entity = self._map_data_entity_from_user_input(user_input, 15)

        await self.async_set_unique_id(self._unique_id(data_entity))
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=data_entity[CONF_FLOW_PIN_NAME],
            data=data_entity,
        )

    # Mappers #

    def _map_data_entity_from_user_input(self, user_input, pin_number):
        return {
            CONF_FLOW_PLATFORM: "switch",
            CONF_FLOW_PIN_NUMBER: pin_number,
            CONF_FLOW_PIN_NAME: self._map_switch_name(user_input,
                                                      pin_number,
                                                      FORM_PIN_NAME_ + str(pin_number)
                                                      ),
            CONF_I2C_ADDRESS: self._map_addr_dic_to_i2caddr(user_input[CONF_FLOW_ADDR]),
        }

    def _map_switch_name(self, user_input, pin_number, pin_name_key=""):
        user_pin_name = self._value_or_empty(user_input, pin_name_key)
        if user_pin_name == "":
            return self._map_entity_id(user_input, pin_number)
        return "%s %s" % (
            self._map_entity_id(user_input, pin_number),
            user_pin_name
        )

    def _map_entity_id(self, user_input, pin_number):
        return "sw_%s_%d" % (
            self._addr_dic_to_title(user_input[CONF_FLOW_ADDR]),
            pin_number + 1,
        )

    def _map_addr_dic_to_i2caddr(self, addr_dic):
        res = 60
        if CONF_FLOW_ADDR_A in addr_dic:
            res += 2 * 2 * 2 * 2 * 2
        if CONF_FLOW_ADDR_B in addr_dic:
            res += 2 * 2 * 2 * 2
        if CONF_FLOW_ADDR_C in addr_dic:
            res += 2 * 2 * 2
        if CONF_FLOW_ADDR_D in addr_dic:
            res += 2 * 2
        if CONF_FLOW_ADDR_E in addr_dic:
            res += 2
        if CONF_FLOW_ADDR_F in addr_dic:
            res += 1
        return res

# class KarismaOptionsFlowHandler(config_entries.OptionsFlow):
#     """Karisma config flow options."""
#
#     def __init__(self, config_entry):
#         """Initialize options flow."""
#         self.config_entry = config_entry
#
#     async def async_step_init(self, user_input=None):
#         """Manage entity options."""
#
#         if user_input is not None:
#
#             return self.async_create_entry(title="", data=user_input)
#
#         data_schema = vol.Schema(
#             {
#                 vol.Optional(
#                     CONF_HW_SYNC,
#                     default=self.config_entry.options.get(
#                         CONF_HW_SYNC, DEFAULT_HW_SYNC
#                     ),
#                 ): bool,
#             }
#         )
#         return self.async_show_form(step_id="init", data_schema=data_schema)
