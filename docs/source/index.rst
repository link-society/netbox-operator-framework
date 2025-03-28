Netbox Operator Framework
=========================

Introduction
------------

`Netbox <https://netboxlabs.com/>`_ is an Open Source CMDB combining IP address
management (IPAM) and Data Center Infrastructure Management (DCIM) capabilities.

It provides *webhooks* to notify external systems about changes in the data
model. This is the basis for infrastructure automation.

The **Netbox Operator Framework** is a Python library, inspired by
`kopf (Kubernetes Operators Framework) <https://kopf.readthedocs.io/>`_, to
create *webhooks* handlers for Netbox.

Example
-------

.. code-block:: python

   from nopf.schema import WebhookPayload
   from nopf.operator import Operator
   from nopf.settings import Settings


   # All settings can be injected via environment variables.
   settings = Settings(
       netbox_api="http://localhost:8080",
       netbox_token="0123456789abcdef0123456789abcdef01234567",
       server_bind_host="0.0.0.0",
       server_bind_port=5000,
       server_callback_name="example",
       server_callback_url="http://localhost:5000",
   )
   op = Operator(settings)


   @op.on_create("dcim.site")
   async def on_site_create(payload: WebhookPayload):
       print(f"Site {payload["data"]["id"]} created")


   @op.on_update("dcim.site")
   async def on_site_update(payload: WebhookPayload):
       print(f"Site {payload["data"]["id"]} updated")


   @op.on_delete("dcim.site")
   async def on_site_delete(payload: WebhookPayload):
       print(f"Site {payload["data"]["id"]} deleted")


   if __name__ == "__main__":
       op.run()

Running this example will automatically create a webhook in Netbox and start
an HTTP server to listen for incoming events.

.. warning::

   The Netbox Operator Framework requires Netbox ``>=3.6.9`` and ``<5.0.0``.

.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   tutorials/webhooks
   tutorials/client
   tutorials/background-tasks
   tutorials/custom-events

.. toctree::
   :maxdepth: 1
   :caption: Design

   design/lifecycle
   design/webhooks

.. toctree::
   :maxdepth: 4
   :caption: API Documentation

   api/nopf
