Webhooks
========

Upon startup, if the environment variable ``NOPF_SECRET_KEY`` (or the
``secret_key`` member of the ``Settings`` class) is not set, a random secret key
will be generated.

This secret key is used by Netbox to sign the webhook requests. It is set on
the webhook object in Netbox at startup. Netbox will then use it to sign the
request body and join the signature via the ``X-Hook-Signature`` HTTP header.

The Operator will then verify the signature before processing the request, and
if invalid, will return a ``403 Forbidden`` response.

The signature algorithm is HMAC-SHA512:

.. code-block:: python

   import hmac
   import hashlib

   content = await request.body()
   signature = hmac.new(
       key=secret_key,    # as bytes
       msg=request_body,  # as bytes
       digestmod=hashlib.sha512,
   ).hexdigest()
