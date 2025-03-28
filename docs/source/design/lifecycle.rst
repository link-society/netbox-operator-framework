Lifecycle
=========

.. mermaid::
   :align: center

   sequenceDiagram
      participant Netbox
      participant Controller

      Controller->>Netbox: Fetch API Schema
      activate Netbox
      Netbox-->>Controller: 200 OK
      deactivate Netbox

      Controller->>Controller: Generate HTTP client

      Controller->>Netbox: Create (or replace) webhooks
      activate Netbox
      Netbox-->>Controller: 201 Created
      deactivate Netbox

      create participant Background Task
      Controller->>Background Task: Start background tasks

      Controller->>Controller: Start HTTP server

      par Webhook Control Loop
         Netbox->>Controller: Notify events via webhook
         activate Controller
         Controller-->>Netbox: 200 OK
         deactivate Controller
      and Background Tasks
         Background Task<<->>External System: Observe External Systems
         Background Task->>Controller: Notify events via internal channel
         activate Controller
         Controller-->>Background Task: Reply via internal channel
         deactivate Controller
      end

      break CTRL+C received
         Controller->>Controller: Stop HTTP server
         destroy Background Task
         Controller-xBackground Task: Cancel background tasks
      end
