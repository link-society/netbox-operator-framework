Handling custom events
======================

In the :ref:`background-tasks` tutorial, you may have noticed the ``tx``
parameter to the task:

.. code-block:: python

   from anyio.abc import TaskStatus
   from anyio import TASK_STATUS_IGNORED

   from nopf.core.channel import ChannelSender
   from nopf.operator import Operator
   from nopf.settings import Settings

   settings = Settings()
   op = Operator(settings)

   @op.task
   async def my_background_task(
       tx: ChannelSender,
       task_status: TaskStatus[None] = TASK_STATUS_IGNORED,
   ):
       # Initialization...

       task_status.started()

       # Observe external system...
       # Use ``NetboxClient.main()`` to interact with Netbox...

This parameter is a producer that can be used to send custom events to the
operator.

You can then receive these events in a custom event handler:

.. code-block:: python

   from anyio.abc import TaskStatus
   from anyio import TASK_STATUS_IGNORED

   from nopf.core.channel import ChannelSender, EventCustom
   from nopf.operator import Operator
   from nopf.settings import Settings

   settings = Settings()
   op = Operator(settings)

   @op.task
   async def on_custom_event(
       tx: ChannelSender,
       task_status: TaskStatus[None] = TASK_STATUS_IGNORED,
   ):
       task_status.started()

       await tx.send(EventCustom(data="Hello, world!"))

   @op.on_custom
   async def handle_custom_event(data: str):
       print(data)

.. note::

   The call to ``tx.send()`` will block until the event is received, whether or
   not you have a handler for it.

   Because the custom event handler executes in the same async task as the
   webhook handlers, it means the call will block until any pending webhook
   handler is done processing the Netbox event.

If an exception is raised in a custom event handler, it will be caught and send
back to the producer, where the call to ``tx.send()`` was made, and raised
there:

.. code-block:: python

   @op.task
   async def on_custom_event(
       tx: ChannelSender,
       task_status: TaskStatus[None] = TASK_STATUS_IGNORED,
   ):
       task_status.started()

       try:
           await tx.send(EventCustom(data="Hello, world!"))

       except RuntimeError as err:
           print("Oops:", err)

   @op.on_custom
   async def handle_custom_event(data: str):
       raise RuntimeError(data)
