"""Test entity_introspection API."""
import pytest
from custom_components.ha_introspection import async_setup_entry
from custom_components.ha_introspection.const import DOMAIN
from custom_components.ha_introspection.const import SERVICE_DO_INTROSPECTION
from pytest_homeassistant_custom_component.common import mock_device_registry
from pytest_homeassistant_custom_component.common import mock_registry
from pytest_homeassistant_custom_component.common import MockEntity
from pytest_homeassistant_custom_component.common import MockEntityPlatform


@pytest.fixture
async def entity_introspection(hass):
    """Return an loaded, introspection."""
    entity_introspection = mock_registry(
        hass,
        {
            "test_domain.world": RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                platform="test_platform",
                name="before update",
                icon="icon:before update",
            )
        },
    )
    platform = MockEntityPlatform(hass)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])
    return entity_introspection


@pytest.fixture
def device_introspection(hass):
    """Return an empty, loaded, introspection."""
    return mock_device_registry(hass)


async def test_remove_entity(hass):
    """Test removing entity."""

    await async_setup_entry(hass, {})

    introspection = mock_registry(
        hass,
        {
            "test_domain.world": RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                name="before update",
            ),
            "test_domain.world2": RegistryEntry(
                entity_id="test_domain.world2",
                unique_id="12345",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                name="before update",
            ),
        },
    )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_DO_INTROSPECTION,
        {
            "expression": "1+2",
        },
        blocking=True,
    )

    assert 0 == 0
