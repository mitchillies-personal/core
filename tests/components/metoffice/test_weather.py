"""The tests for the Met Office sensor component."""
from datetime import timedelta
import json
from unittest.mock import patch

from homeassistant.components.metoffice.const import DOMAIN
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers.device_registry import async_get as get_dev_reg
from homeassistant.util import utcnow

from . import NewDateTime
from .const import (
    DEVICE_KEY_KINGSLYNN,
    DEVICE_KEY_WAVERTREE,
    METOFFICE_CONFIG_KINGSLYNN,
    METOFFICE_CONFIG_WAVERTREE,
    WAVERTREE_SENSOR_RESULTS,
)

from tests.common import MockConfigEntry, async_fire_time_changed, load_fixture


@patch(
    "datapoint.Forecast.datetime.datetime",
    NewDateTime,
)
async def test_site_cannot_connect(hass, requests_mock, legacy_patchable_time):
    """Test we handle cannot connect error."""

    requests_mock.get("/public/data/val/wxfcs/all/json/sitelist/", text="")
    requests_mock.get("/public/data/val/wxfcs/all/json/354107?res=3hourly", text="")
    requests_mock.get("/public/data/val/wxfcs/all/json/354107?res=daily", text="")

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    dev_reg = get_dev_reg(hass)
    assert len(dev_reg.devices) == 0

    assert hass.states.get("weather.met_office_wavertree_3hourly") is None
    assert hass.states.get("weather.met_office_wavertree_daily") is None
    for sensor_id in WAVERTREE_SENSOR_RESULTS:
        sensor_name, _ = WAVERTREE_SENSOR_RESULTS[sensor_id]
        sensor = hass.states.get(f"sensor.wavertree_{sensor_name}")
        assert sensor is None


@patch(
    "datapoint.Forecast.datetime.datetime",
    NewDateTime,
)
async def test_site_cannot_update(hass, requests_mock, legacy_patchable_time):
    """Test we handle cannot connect error."""

    # all metoffice test data encapsulated in here
    mock_json = json.loads(load_fixture("metoffice.json"))
    all_sites = json.dumps(mock_json["all_sites"])
    wavertree_hourly = json.dumps(mock_json["wavertree_hourly"])
    wavertree_daily = json.dumps(mock_json["wavertree_daily"])

    requests_mock.get("/public/data/val/wxfcs/all/json/sitelist/", text=all_sites)
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/354107?res=3hourly", text=wavertree_hourly
    )
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/354107?res=daily", text=wavertree_daily
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    weather = hass.states.get("weather.met_office_wavertree_3_hourly")
    assert weather

    weather = hass.states.get("weather.met_office_wavertree_daily")
    assert weather

    requests_mock.get("/public/data/val/wxfcs/all/json/354107?res=3hourly", text="")
    requests_mock.get("/public/data/val/wxfcs/all/json/354107?res=daily", text="")

    future_time = utcnow() + timedelta(minutes=20)
    async_fire_time_changed(hass, future_time)
    await hass.async_block_till_done()

    weather = hass.states.get("weather.met_office_wavertree_3_hourly")
    assert weather.state == STATE_UNAVAILABLE

    weather = hass.states.get("weather.met_office_wavertree_daily")
    assert weather.state == STATE_UNAVAILABLE


@patch(
    "datapoint.Forecast.datetime.datetime",
    NewDateTime,
)
async def test_one_weather_site_running(hass, requests_mock, legacy_patchable_time):
    """Test the Met Office weather platform."""

    # all metoffice test data encapsulated in here
    mock_json = json.loads(load_fixture("metoffice.json"))
    all_sites = json.dumps(mock_json["all_sites"])
    wavertree_hourly = json.dumps(mock_json["wavertree_hourly"])
    wavertree_daily = json.dumps(mock_json["wavertree_daily"])

    requests_mock.get("/public/data/val/wxfcs/all/json/sitelist/", text=all_sites)
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/354107?res=3hourly",
        text=wavertree_hourly,
    )
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/354107?res=daily",
        text=wavertree_daily,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    dev_reg = get_dev_reg(hass)
    assert len(dev_reg.devices) == 1
    device_wavertree = dev_reg.async_get_device(identifiers=DEVICE_KEY_WAVERTREE)
    assert device_wavertree.name == "Met Office Wavertree"

    # Wavertree 3-hourly weather platform expected results
    weather = hass.states.get("weather.met_office_wavertree_3_hourly")
    assert weather

    assert weather.state == "sunny"
    assert weather.attributes.get("temperature") == 17
    assert weather.attributes.get("wind_speed") == 9
    assert weather.attributes.get("wind_bearing") == "SSE"
    assert weather.attributes.get("visibility") == "Good - 10-20"
    assert weather.attributes.get("humidity") == 50

    # Forecasts added - just pick out 1 entry to check
    assert len(weather.attributes.get("forecast")) == 35

    assert (
        weather.attributes.get("forecast")[26]["datetime"]
        == "2020-04-28T21:00:00+00:00"
    )
    assert weather.attributes.get("forecast")[26]["condition"] == "cloudy"
    assert weather.attributes.get("forecast")[26]["precipitation_probability"] == 9
    assert weather.attributes.get("forecast")[26]["temperature"] == 10
    assert weather.attributes.get("forecast")[26]["wind_speed"] == 4
    assert weather.attributes.get("forecast")[26]["wind_bearing"] == "NNE"

    # Wavertree daily weather platform expected results
    weather = hass.states.get("weather.met_office_wavertree_daily")
    assert weather

    assert weather.state == "sunny"
    assert weather.attributes.get("temperature") == 19
    assert weather.attributes.get("wind_speed") == 9
    assert weather.attributes.get("wind_bearing") == "SSE"
    assert weather.attributes.get("visibility") == "Good - 10-20"
    assert weather.attributes.get("humidity") == 50

    # Also has Forecasts added - again, just pick out 1 entry to check
    assert len(weather.attributes.get("forecast")) == 8

    assert (
        weather.attributes.get("forecast")[7]["datetime"] == "2020-04-29T12:00:00+00:00"
    )
    assert weather.attributes.get("forecast")[7]["condition"] == "rainy"
    assert weather.attributes.get("forecast")[7]["precipitation_probability"] == 59
    assert weather.attributes.get("forecast")[7]["temperature"] == 13
    assert weather.attributes.get("forecast")[7]["wind_speed"] == 13
    assert weather.attributes.get("forecast")[7]["wind_bearing"] == "SE"
    assert weather.attributes.get("forecast")[7]["daytime"] is True

    # Check that night entry is correctly marked as Night
    assert (
        weather.attributes.get("forecast")[6]["datetime"] == "2020-04-29T00:00:00+00:00"
    )
    assert weather.attributes.get("forecast")[6]["daytime"] is False


@patch(
    "datapoint.Forecast.datetime.datetime",
    NewDateTime,
)
async def test_two_weather_sites_running(hass, requests_mock, legacy_patchable_time):
    """Test we handle two different weather sites both running."""

    # all metoffice test data encapsulated in here
    mock_json = json.loads(load_fixture("metoffice.json"))
    all_sites = json.dumps(mock_json["all_sites"])
    wavertree_hourly = json.dumps(mock_json["wavertree_hourly"])
    wavertree_daily = json.dumps(mock_json["wavertree_daily"])
    kingslynn_hourly = json.dumps(mock_json["kingslynn_hourly"])
    kingslynn_daily = json.dumps(mock_json["kingslynn_daily"])

    requests_mock.get("/public/data/val/wxfcs/all/json/sitelist/", text=all_sites)
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/354107?res=3hourly", text=wavertree_hourly
    )
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/354107?res=daily", text=wavertree_daily
    )
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/322380?res=3hourly", text=kingslynn_hourly
    )
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/322380?res=daily", text=kingslynn_daily
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_KINGSLYNN,
    )
    entry2.add_to_hass(hass)
    await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()

    dev_reg = get_dev_reg(hass)
    assert len(dev_reg.devices) == 2
    device_kingslynn = dev_reg.async_get_device(identifiers=DEVICE_KEY_KINGSLYNN)
    assert device_kingslynn.name == "Met Office King's Lynn"
    device_wavertree = dev_reg.async_get_device(identifiers=DEVICE_KEY_WAVERTREE)
    assert device_wavertree.name == "Met Office Wavertree"

    # Wavertree 3-hourly weather platform expected results
    weather = hass.states.get("weather.met_office_wavertree_3_hourly")
    assert weather

    assert weather.state == "sunny"
    assert weather.attributes.get("temperature") == 17
    assert weather.attributes.get("wind_speed") == 9
    assert weather.attributes.get("wind_bearing") == "SSE"
    assert weather.attributes.get("visibility") == "Good - 10-20"
    assert weather.attributes.get("humidity") == 50

    # Forecasts added - just pick out 1 entry to check
    assert len(weather.attributes.get("forecast")) == 35

    assert (
        weather.attributes.get("forecast")[18]["datetime"]
        == "2020-04-27T21:00:00+00:00"
    )
    assert weather.attributes.get("forecast")[18]["condition"] == "clear-night"
    assert weather.attributes.get("forecast")[18]["precipitation_probability"] == 1
    assert weather.attributes.get("forecast")[18]["temperature"] == 9
    assert weather.attributes.get("forecast")[18]["wind_speed"] == 4
    assert weather.attributes.get("forecast")[18]["wind_bearing"] == "NW"
    assert "daytime" not in weather.attributes.get("forecast")[18]

    # Wavertree daily weather platform expected results
    weather = hass.states.get("weather.met_office_wavertree_daily")
    assert weather

    assert weather.state == "sunny"
    assert weather.attributes.get("temperature") == 19
    assert weather.attributes.get("wind_speed") == 9
    assert weather.attributes.get("wind_bearing") == "SSE"
    assert weather.attributes.get("visibility") == "Good - 10-20"
    assert weather.attributes.get("humidity") == 50

    # Also has Forecasts added - again, just pick out 1 entry to check
    assert len(weather.attributes.get("forecast")) == 8

    assert (
        weather.attributes.get("forecast")[7]["datetime"] == "2020-04-29T12:00:00+00:00"
    )
    assert weather.attributes.get("forecast")[7]["condition"] == "rainy"
    assert weather.attributes.get("forecast")[7]["precipitation_probability"] == 59
    assert weather.attributes.get("forecast")[7]["temperature"] == 13
    assert weather.attributes.get("forecast")[7]["wind_speed"] == 13
    assert weather.attributes.get("forecast")[7]["wind_bearing"] == "SE"
    assert weather.attributes.get("forecast")[7]["daytime"] is True

    # King's Lynn 3-hourly weather platform expected results
    weather = hass.states.get("weather.met_office_king_s_lynn_3_hourly")
    assert weather

    assert weather.state == "sunny"
    assert weather.attributes.get("temperature") == 14
    assert weather.attributes.get("wind_speed") == 2
    assert weather.attributes.get("wind_bearing") == "E"
    assert weather.attributes.get("visibility") == "Very Good - 20-40"
    assert weather.attributes.get("humidity") == 60

    # Also has Forecast added - just pick out 1 entry to check
    assert len(weather.attributes.get("forecast")) == 35

    assert (
        weather.attributes.get("forecast")[18]["datetime"]
        == "2020-04-27T21:00:00+00:00"
    )
    assert weather.attributes.get("forecast")[18]["condition"] == "cloudy"
    assert weather.attributes.get("forecast")[18]["precipitation_probability"] == 9
    assert weather.attributes.get("forecast")[18]["temperature"] == 10
    assert weather.attributes.get("forecast")[18]["wind_speed"] == 7
    assert weather.attributes.get("forecast")[18]["wind_bearing"] == "SE"
    assert "daytime" not in weather.attributes.get("forecast")[18]

    # King's Lynn daily weather platform expected results
    weather = hass.states.get("weather.met_office_king_s_lynn_daily")
    assert weather

    assert weather.state == "cloudy"
    assert weather.attributes.get("temperature") == 9
    assert weather.attributes.get("wind_speed") == 4
    assert weather.attributes.get("wind_bearing") == "ESE"
    assert weather.attributes.get("visibility") == "Very Good - 20-40"
    assert weather.attributes.get("humidity") == 75

    # All should have Forecast added - again, just picking out 1 entry to check
    assert len(weather.attributes.get("forecast")) == 8

    assert (
        weather.attributes.get("forecast")[5]["datetime"] == "2020-04-28T12:00:00+00:00"
    )
    assert weather.attributes.get("forecast")[5]["condition"] == "cloudy"
    assert weather.attributes.get("forecast")[5]["precipitation_probability"] == 14
    assert weather.attributes.get("forecast")[5]["temperature"] == 11
    assert weather.attributes.get("forecast")[5]["wind_speed"] == 7
    assert weather.attributes.get("forecast")[5]["wind_bearing"] == "ESE"
    assert weather.attributes.get("forecast")[5]["daytime"] is True
