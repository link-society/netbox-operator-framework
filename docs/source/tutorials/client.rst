Netbox HTTP Client
==================

Instanciation
-------------

Upon startup, the Netbox Operator Framework will fetch the Netbox API Schema
from the Netbox instance. It is then used to generate the HTTP client at startup.

.. note::

   This step can be slow. Netbox can take some time to return the API schema.
   You can however pre-fetch the schema and specify it via the ``NETBOX_SCHEMA``
   environment variable (or the ``netbox_schema`` member of the ``Settings``
   class), this would help speedup the startup time.

   While loading a YAML-encoded schema is supported, it is also slower than
   loading a JSON-encoded schema.

You can instantiate a new HTTP client by supplying the operator Settings to the
class constructor:

.. code-block:: python

   from nopf.settings import Settings
   from nopf.client import NetboxClient

   settings = Settings()
   client = NetboxClient(settings)

But to avoid constently re-fetching / re-generating the client, the Operator
provides a singleton instance of the client, accessible from any webhook handler
or task:

.. code-block:: python

   from nopf.settings import Settings
   from nopf.operator import Operator
   from nopf.schema import WebhookPayload
   from nopf.client import NetboxClient

   settings = Settings()
   op = Operator(settings)

   @op.on_create("dcim.site")
   async def on_site_create(site: WebhookPayload):
       client = NetboxClient.main()
       # ...

API Information
---------------

The ``NetboxClient`` class provides a few properties to access the API metadata:

* ``title``: the API title (corresponds to the schema's ``#/info/title`` property)
* ``version``: the API version (corresponds to the schema's ``#/info/version`` property)
* ``license``: the API license (corresponds to the schema's ``#/info/license/name`` property)

.. code-block:: python

   title = client.title
   version_major = client.version.major
   version_minor = client.version.minor
   version_patch = client.version.patch
   license = client.license

Operations
----------

All operations defined in the OpenAPI schema are available as async methods on
the ``operations`` property:

.. code-block:: python

   resp = await client.operations.dcim_sites_create(body={
       "name": "Site 1",
       "slug": "site-1",
   })

.. note::

   The method name is the ID of the operation as it appears in the OpenAPI
   schema.

Each operation take 2 arguments:

* ``body``: the request body, as a dictionary
* ``params``: the path and query parameters, as a dictionary

They will be validated against the OpenAPI schema before being sent to Netbox:

.. code-block:: python

   import jsonschema

   try:
       resp = await client.operations.dcim_sites_create()

   except jsonschema.ValidationError as err:
       print(f"Validation error: {err}")

The response will also be validated after being received from Netbox, just in
case the loaded OpenAPI schema does not match the actual Netbox instance (which
could happen if you use a pre-fetched schema).

For more information about the ``Response`` object, please consult the
`httpx documentation <https://www.python-httpx.org/api/#response>`_.

.. note::

   Every request and response is logged automatically.
