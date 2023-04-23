HA_HOST="$1"
token="$2"


# introspect.sh
# simple example of using the ha_introspection custom_component

# define your own library functions on the fly:
lib="
import inspect
def no_(a): 
    return [ e for e in a if not e.startswith('_') ]

def head(a,cnt=20): 
    return a[:cnt]

def fmt(a):
    result=''
    for n in a:
        result += str(n) + '\n'
    return result
"
expr=$( sed -e 's/\\/\\\\/g' -e "s/'/\\\'/g" -e "s/,/\\\,/g" <<<"$3" )
lib=$( sed -e 's/\\/\\\\/g' -e "s/'/\\\'/g" -e "s/,/\\\,/g" <<<"$lib" )
fetch="{% for i in range(1+states.introspection.len.state|int) %}{{  states.introspection['result_' ~ i]['state'] }}{% endfor %}"

hass-cli -o json -x -s http://$HA_HOST:8123 --token $token service call ha_introspection.do_introspection --arguments statement="$lib",expression="$expr" >/dev/null
hass-cli -o json -x -s http://$HA_HOST:8123 --token $token template <(echo "$fetch")


###########################################################
# example uses:

# introspect.sh $HOST $TOKEN  "dir()"
# ['call', 'expression', 'hass']

# introspect.sh $HOST $TOKEN "[e for e in dir(hass)[12:] if not e.startswith('_')]"
# ['add_job', 'async_add_executor_job', 'async_add_hass_job', 'async_add_job',...

# introspect.sh $HOST $TOKEN "[e for e in dir(hass.components) if not e.startswith('_')]"
# ['frontend', 'group', 'hassio', 'webhook', 'websocket_api']
###########################################################
