Writing Webhook handlers
========================

Webhooks are triggered upon creation, update, or deletion of objects in Netbox.
The Netbox Operator Framework allows you to simply setup handlers to those
events and filter by object types:

.. code-block:: python

   from nopf.schema import WebhookPayload
   from nopf.operator import Operator
   from nopf.settings import Settings

   settings = Settings()
   op = Operator()

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


* the ``@op.on_create`` hook will register the function to be called when a new
  ``dcim.site`` object is created
* the ``@op.on_update`` hook will register the function to be called when an
  existing ``dcim.site`` object is updated
* the ``@op.on_delete`` hook will register the function to be called when an
  existing ``dcim.site`` object is deleted

The string argument to the decorator is the object type to filter by. In Django
terms (because Netbox is written in Django), this is the "content type", the
name of the model with its namespace.

Netbox Plugins are automatically supported, here is an example with the
`Netbox Docker Plugin <https://github.com/SaaShup/netbox-docker-plugin>`_:

.. code-block:: python

   from nopf.schema import WebhookPayload
   from nopf.operator import Operator
   from nopf.settings import Settings

   settings = Settings()
   op = Operator()

   @op.on_create("netbox_docker_plugin.container")
   async def on_container_create(payload: WebhookPayload):
       print(f"Docker Container {payload["data"]["id"]} created")

   @op.on_update("netbox_docker_plugin.container")
   async def on_container_update(payload: WebhookPayload):
       print(f"Docker Container {payload["data"]["id"]} updated")

   @op.on_delete("netbox_docker_plugin.container")
   async def on_container_delete(payload: WebhookPayload):
       print(f"Docker Container {payload["data"]["id"]} deleted")

   if __name__ == "__main__":
       op.run()


The ``WebhookPayload`` object is a dictionary that contains the body of the
webhook request, more information about its content can be found in the
`Netbox Webhook Documentation <https://netboxlabs.com/docs/netbox/en/stable/integrations/webhooks/#default-request-body>`_.

.. note::

   The Netbox Operator Framework uses `anyio <https://anyio.readthedocs.io/>`_
   with the native `asyncio <https://docs.python.org/3/library/asyncio.html>`_
   backend.

If an exception is raised in a handler, the operator will return to Netbox
a 500 HTTP status code with the exception message as the response body.
