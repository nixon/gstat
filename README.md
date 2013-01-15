# gstat

Send metrics to a graphite host without causing any exceptions or
otherwise preventing the caller from continuing.

## Configuration

Use environment variables to control where metrics are sent:

```
   CARBON_HOST:  if not set, logs metrics instead of sending to a host (useful during development, etc)
   CARBON_PORT:  defaults to 2003
```

## Installation

 * python setup.py install

## Testing

 * pip install -r requirements.pip
 * nosetests
