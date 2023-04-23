# Home Assistant Introspection

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

[![Community Forum][forum-shield]][forum]

## Description

Adds a service for Home Assistant to do dynamic introspection with python expressions.

> **WARNING**: This is a very powerful low-level tool for inspecting (and possibly changing) the internal environment in the running Home Assistant system. There are no safeguards, and this should be used only if you fully understand the consequences of running "eval()" with whatever arbitrary python code you submit, inside of the running Home Assistant process.

It's entirely likely HA core will never support such low-level direct access as what's provided in this simple integration. You can use HACS to install this integration manually as explained below.

### Services

#### Do Introspection

Evaluate a piece of python code in the context of the running Home Assistant process.

`expression` is a string with they python code you wish to `eval`
`statement` is an optional string with python code you want exec'd first, before the eval (good for declaring functions).

```yaml
service: ha_introspection.do_introspection
data:
  statement: "def head(s): return s[20:]"
  expression: head(dir())
```
The results of the eval'd expression are stashed in state(s), for lack of a better way for a service to return results. (Please le me know if there is a more straightforward approach.) Since every state value is limited to 255 bytes, a long result could overflow, so multiples states may be used. You'll find the count of states populated `instrospection.len`, indicating the maximum "n" for the values stored in `instrospection.state_(n)`. If the result is less than 256 bytes, there's just introspection.state_1.

Because every call to do_introspection might change the values of one or many states, you are advised to exclude them from recorder, with this in your configuration.yaml:

```yaml
recorder:
  exclude:
    entity_globs:
      - introspection.*
```

The following template can be used to concatenate all of the states to get the result of the do_introspection eval:

```
{% for i in range(1+states.introspection.len.state|int) %}{{  states.introspection['result_' ~ i]['state'] }}{% endfor %}
```

An example shell script which invokes the do_introspection service and then fetches the results via the template is available in the project, as "introspect.sh".

{% if not installed %}

## Installation
For now, you'll need to add a "custom repository," https://github.com/homeautomaton/ha-introspection in the HACS menu at the top, then the integration will show up for "download." 

{% endif %}


## Contributions are welcome!

TBD

## Credits

Inspiration and some formatting/logic taken from [@amosyuen]([user_profile]: https://github.com/amosyuen)'s ha-registry

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/homeautomaton/ha-introspection.svg?style=for-the-badge
[commits]: https://github.com/homeautomaton/ha-introspection/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/homeautomaton/ha-introspection.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40homeautomaton-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/homeautomaton/ha-introspection.svg?style=for-the-badge
[releases]: https://github.com/homeautomaton/ha-introspection/releases
[user_profile]: https://github.com/homeautomaton
