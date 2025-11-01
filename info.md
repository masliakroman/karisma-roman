[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

[Karisma Custom Component](https://github.com/Girani/karisma)

Custom component for the Karisma relay.

## Highlights of what it does offer

- **Async** implementation (more reactive and nicer to HA)
- **Thread-safety** allows different entities to use the same component
- **Config Flow** support (UI configuration) in addition to legacy configuration.yaml.
- **Push iso pull model** for higher reactivity, e.g. 100ms polling for 'zero-delay' push button without loading HA.
- Optimized i2c bus bandwidth utilisation
  - Polling per device instead of per entity/8x gain, register cache to avoid read-modify-write/3xgain or rewriting the same register value)
- Synchronization with the device state at startup, e.g. avoid output glitches when HA restart.

## Useful links

- [Repository](https://github.com/Girani/karisma)
- [Forked MCP23017 repository](https://github.com/jpcornil-git/HA-mcp23017)
- [MCP23017 component](https://www.microchip.com/wwwproducts/en/mcp23017)
- [RPi GPIO expander](https://github.com/jpcornil-git/RPiHat_GPIO_Expander)
