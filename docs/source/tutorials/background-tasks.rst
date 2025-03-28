.. _background-tasks:

Running tasks in the background
===============================

Often, a Netbox Operator has to interact with an external system that can
produce events. The operator listens to those events and might create, update
or delete objects in Netbox, which can in turn trigger other webhooks.

The Netbox Operator Framework provides a decorator to register a task to be run
in parallel (concurrently) of the HTTP server:

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

As soon as the function returns, the task terminates. If you want to keep the
task running indefinitely, you can use a loop.

.. warning::

   The ``task_status.started()`` method must be called to signal that the task
   has started. Otherwise, the operator will wait indefinitely for the task to
   start.

.. warning::

   An exception raised in a background task will terminate the operator as a
   whole, so make sure to handle exceptions properly.
