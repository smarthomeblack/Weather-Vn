"""Config flow for Weather Vn integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from .const import (
    DOMAIN,
    PROVINCES,
    DISTRICTS,
    CONF_PROVINCE,
    CONF_DISTRICT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    _load_json_data_sync,
    _load_json_data_async,
)


class WeatherVnConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Weather Vn."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return WeatherVnOptionsFlow(config_entry)

    def __init__(self):
        """Initialize the config flow."""
        self._province = None
        self._districts = {}
        self._scan_interval = DEFAULT_SCAN_INTERVAL

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step to select province."""
        errors = {}

        if user_input is not None:
            self._province = user_input[CONF_PROVINCE]
            return await self.async_step_district()

        provinces_list = {k: v for k, v in PROVINCES.items()}

        schema = vol.Schema(
            {
                vol.Required(CONF_PROVINCE): vol.In(provinces_list),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_district(self, user_input=None) -> FlowResult:
        """Handle the district selection step."""
        errors = {}

        if user_input is not None:
            province = self._province
            district = user_input[CONF_DISTRICT]

            # Kiểm tra xem đã cấu hình tỉnh/huyện này chưa
            await self.async_set_unique_id(f"{province}-{district}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{PROVINCES.get(province, province)} - {DISTRICTS.get(district, district)}",
                data={
                    CONF_PROVINCE: province,
                    CONF_DISTRICT: district,
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,  # Thêm giá trị mặc định cho scan_interval
                },
            )

        # Lấy danh sách quận/huyện từ file JSON - sử dụng phiên bản async
        province_districts = await self._get_districts_for_province(self._province)

        # Nếu không tìm thấy quận/huyện nào, hiển thị tất cả
        if not province_districts:
            available_districts = {k: v for k, v in DISTRICTS.items()}
        else:
            available_districts = province_districts

        schema = vol.Schema(
            {
                vol.Required(CONF_DISTRICT): vol.In(available_districts),
            }
        )

        return self.async_show_form(
            step_id="district", data_schema=schema, errors=errors
        )

    async def _get_districts_for_province(self, province_id):
        """Lấy danh sách quận/huyện của một tỉnh từ file JSON."""
        try:
            data = await _load_json_data_async(self.hass, "provinces_districts.json")
            if province_id in data:
                return data[province_id].get("districts", {})
        except Exception:
            # Nếu gặp lỗi khi đọc file bằng async, dùng phương thức đồng bộ backup
            data = _load_json_data_sync("provinces_districts.json")
            if province_id in data:
                return data[province_id].get("districts", {})
        return {}


class WeatherVnOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Weather Vn integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # Thay vì lưu config_entry, lưu các dữ liệu cần thiết
        self._entry_data = config_entry.data
        self._province = None
        self._scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options - first select province."""
        if user_input is not None:
            self._province = user_input[CONF_PROVINCE]
            self._scan_interval = user_input[CONF_SCAN_INTERVAL]
            return await self.async_step_district()

        provinces_list = {k: v for k, v in PROVINCES.items()}

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PROVINCE,
                    default=self._entry_data.get(CONF_PROVINCE),
                ): vol.In(provinces_list),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self._scan_interval,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=5,
                        max=180,
                        step=5,
                        mode=selector.NumberSelectorMode.SLIDER,
                        unit_of_measurement="phút",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=schema
        )

    async def async_step_district(self, user_input=None) -> FlowResult:
        """Handle the district selection in options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_PROVINCE: self._province,
                    CONF_DISTRICT: user_input[CONF_DISTRICT],
                    CONF_SCAN_INTERVAL: self._scan_interval,
                },
            )

        # Lấy danh sách quận/huyện từ file JSON - sử dụng phiên bản async
        province_districts = await self._get_districts_for_province(self._province)

        # Nếu không tìm thấy quận/huyện nào, hiển thị tất cả
        if not province_districts:
            available_districts = {k: v for k, v in DISTRICTS.items()}
        else:
            available_districts = province_districts

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DISTRICT,
                    default=self._entry_data.get(CONF_DISTRICT),
                ): vol.In(available_districts),
            }
        )

        return self.async_show_form(
            step_id="district", data_schema=schema
        )

    async def _get_districts_for_province(self, province_id):
        """Lấy danh sách quận/huyện của một tỉnh từ file JSON."""
        try:
            data = await _load_json_data_async(self.hass, "provinces_districts.json")
            if province_id in data:
                return data[province_id].get("districts", {})
        except Exception:
            # Nếu gặp lỗi khi đọc file bằng async, dùng phương thức đồng bộ backup
            data = _load_json_data_sync("provinces_districts.json")
            if province_id in data:
                return data[province_id].get("districts", {})
        return {}
