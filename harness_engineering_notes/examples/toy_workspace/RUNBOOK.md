# Agent harness engineering notes

Internal wiki for checkout-service.

Owner: platform
On-call: #infra-oncall
SLO: 99.9% availability, p99 checkout < 400ms

Known incidents:
- 2026-04-12: payment-gateway timeouts after TLS rotation
- 2026-07-03: cart cache stampeded when Redis failover lagged
