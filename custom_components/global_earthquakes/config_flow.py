import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_INSTANCE_NAME,
    CONF_MONITORED_COUNTRIES,
    CONF_SCAN_INTERVAL,
    CONF_MIN_MAG_USA,
    CONF_MIN_MAG_GLOBAL,
    CONF_MAP_MARKERS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MIN_MAG_USA,
    DEFAULT_MIN_MAG_GLOBAL,
    DEFAULT_MAP_MARKERS,
)

_LOGGER = logging.getLogger(__name__)

COUNTRY_OPTIONS = [
    {"value": "ALL", "label": "Worldwide (All Countries)"},
    {"value": "EUROPE", "label": "Europe (All Countries Group)"},
    # --- Major Global Regions ---
    {"value": "USA", "label": "United States"},
    {"value": "Japan", "label": "Japan"},
    {"value": "Indonesia", "label": "Indonesia"},
    {"value": "Mexico", "label": "Mexico"},
    {"value": "Chile", "label": "Chile"},
    {"value": "New Zealand", "label": "New Zealand"},
    # --- Southern & Eastern Europe (High Seismic Activity) ---
    {"value": "Albania", "label": "Albania"},
    {"value": "Bosnia and Herzegovina", "label": "Bosnia & Herzegovina"},
    {"value": "Bulgaria", "label": "Bulgaria"},
    {"value": "Croatia", "label": "Croatia"},
    {"value": "Cyprus", "label": "Cyprus"},
    {"value": "Greece", "label": "Greece"},
    {"value": "Iceland", "label": "Iceland"},
    {"value": "Italy", "label": "Italy"},
    {"value": "Montenegro", "label": "Montenegro"},
    {"value": "North Macedonia", "label": "North Macedonia"},
    {"value": "Portugal", "label": "Portugal"},
    {"value": "Romania", "label": "Romania"},
    {"value": "Serbia", "label": "Serbia"},
    {"value": "Slovenia", "label": "Slovenia"},
    {"value": "Spain", "label": "Spain"},
    {"value": "Turkey", "label": "Turkey"},
    # --- Western & Northern Europe ---
    {"value": "Austria", "label": "Austria"},
    {"value": "Belgium", "label": "Belgium"},
    {"value": "Czechia", "label": "Czechia"},
    {"value": "Denmark", "label": "Denmark"},
    {"value": "Finland", "label": "Finland"},
    {"value": "France", "label": "France"},
    {"value": "Germany", "label": "Germany"},
    {"value": "Hungary", "label": "Hungary"},
    {"value": "Ireland", "label": "Ireland"},
    {"value": "Luxembourg", "label": "Luxembourg"},
    {"value": "Netherlands", "label": "Netherlands"},
    {"value": "Norway", "label": "Norway"},
    {"value": "Poland", "label": "Poland"},
    {"value": "Slovakia", "label": "Slovakia"},
    {"value": "Sweden", "label": "Sweden"},
    {"value": "Switzerland", "label": "Switzerland"},
    {"value": "United Kingdom", "label": "United Kingdom"},
    # --- Baltic & Eastern Margin ---
    {"value": "Belarus", "label": "Belarus"},
    {"value": "Estonia", "label": "Estonia"},
    {"value": "Latvia", "label": "Latvia"},
    {"value": "Lithuania", "label": "Lithuania"},
    {"value": "Malta", "label": "Malta"},
    {"value": "Moldova", "label": "Moldova"},
    {"value": "Ukraine", "label": "Ukraine"},
]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title=f"Earthquakes ({user_input[CONF_INSTANCE_NAME]})",
                data=user_input,
                options=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_INSTANCE_NAME, default="Global Tracker"): str,
                vol.Required(CONF_MIN_MAG_USA, default=DEFAULT_MIN_MAG_USA): vol.Coerce(
                    float
                ),
                vol.Required(
                    CONF_MIN_MAG_GLOBAL, default=DEFAULT_MIN_MAG_GLOBAL
                ): vol.Coerce(float),
                vol.Required(
                    CONF_MONITORED_COUNTRIES, default=["ALL"]
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=COUNTRY_OPTIONS,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_MAP_MARKERS, default=DEFAULT_MAP_MARKERS
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=50, step=1, mode=selector.NumberSelectorMode.SLIDER
                    )
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_MIN_MAG_USA,
                    default=self.config_entry.options.get(
                        CONF_MIN_MAG_USA, DEFAULT_MIN_MAG_USA
                    ),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_MIN_MAG_GLOBAL,
                    default=self.config_entry.options.get(
                        CONF_MIN_MAG_GLOBAL, DEFAULT_MIN_MAG_GLOBAL
                    ),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_MONITORED_COUNTRIES,
                    default=self.config_entry.options.get(
                        CONF_MONITORED_COUNTRIES, ["ALL"]
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=COUNTRY_OPTIONS,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_MAP_MARKERS,
                    default=self.config_entry.options.get(
                        CONF_MAP_MARKERS, DEFAULT_MAP_MARKERS
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=50, step=1, mode=selector.NumberSelectorMode.SLIDER
                    )
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
