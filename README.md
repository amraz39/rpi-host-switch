# Switching public hostnames after cloning a Raspberry Pi

> **Starting reference, not a ready-to-use solution.** This repository provides guidance and tested examples for identifying a Pi and deciding what should happen at startup. It does not include a complete installer or automatically perform hostname changes. Before using this approach, you must build and test the startup service, configuration updates, backups, rollback, certificate handling and container checks for your own system.

This guide describes a cautious approach for maintaining two Raspberry Pis at different locations. One Pi is the source system; a periodically refreshed copy runs on the second Pi with a different public hostname. It is a design guide, not an installer or a guarantee that a cloned system will work unchanged.

## Example Python component

`board_identity.py` is a read-only example that checks the Raspberry Pi 5 model and compares two device-tree serial properties. `test_board_identity.py` tests it against synthetic device-tree files; run the tests with `python3 -B test_board_identity.py` (or `python -B test_board_identity.py` on Windows). The example is a library, not a command that configures a Pi or performs a hostname switch. It supports a deliberately narrow model/property format; other boards or firmware may fail the check and need review. The two properties are software-visible views, not independent protection against a modified device tree. Do not publish the actual serial number when using this code.

`startup_decision.py` illustrates how to decide whether to skip, prepare, recover or wait based on the board and saved transaction state. Its serial number and hostname are example placeholders. Test it with `python3 -B test_startup_decision.py`. This is only a decision model: it does not install a service, authenticate or persist state, back up files, change hostnames, renew certificates, or implement rollback. Those pieces must be designed and tested separately before any production use.

## Intended behavior

1. The source Pi retains its existing settings on every boot.
2. The cloned system identifies the destination Pi using a hardware-specific identifier, not a disk or partition UUID.
3. On the destination's first boot after a fresh clone, the switch backs up and checks the settings it plans to change, then updates the destination's public hostname.
4. Later destination boots do not repeat a successful switch. A failed switch should restore the saved settings and stop for review.

If the hardware identifier cannot be read or validated, stop without changing anything. A replacement source board needs an explicit review: blindly treating any different identifier as the destination can switch the wrong machine. Store completion state on the cloned system and account for the fact that each new clone replaces the destination's prior state.

## Before making a switch

- Keep an independent, verified backup. A live filesystem copy is not necessarily a consistent backup of databases or applications with active writers; use application-supported backups or quiesce them first.
- Inventory the hostname in active web-server and application configuration, service definitions, scheduled jobs and certificate settings. Exclude logs and old backups from automatic edits. Do not assume every reference is plain text or safe to replace.
- Review each proposed change and save the original file, permissions and relevant metadata in a protected location. Validate the backups before changing anything. Test recovery, including interruption during the update.
- Validate web-server configurations before applying them, and check relevant service health afterward. If validation fails, restore the saved settings. Ensure local or out-of-band access is available: rollback alone cannot guarantee that remote access will survive.
- Treat DNS, router forwarding and certificate issuance as separate prerequisites. The destination needs a certificate valid for its own hostname and a working renewal method. A network or certificate-provider outage may need retry rather than rollback of unrelated settings.

## Containers and applications

Container environment variables, bind mounts, stacks, application databases and web-based settings may all contain hostnames. A read-only inventory can help identify candidates, but it may miss databases, encrypted data, inaccessible files or values generated at runtime. Review and update the affected stacks and applications through their supported interfaces; preserve the URL scheme, port and path. Review login, OAuth, webhooks and integrations separately.

If a container maintains its own certificate copy, renewing the host certificate may not update that copy. Check the application's documented certificate deployment process and repeat it when the certificate renews.

## Copy and destination checks

When using Raspberry Pi OS SD Card Copier, select the intended source and destination carefully; the destination will be overwritten. Use the **New Partition UUIDs** option when appropriate for the copy. After booting the destination at its location, verify the switch status, public DNS, certificate, web access, application logins and integrations. Repeat the application review after each new clone.

## Privacy and safety

Do not publish private keys, passwords, access tokens, backups, real network addresses, hardware identifiers or unredacted configuration inventories. Replace site-specific details before sharing. The full original implementation for a particular installation is intentionally not included here: its paths, services and safety assumptions are specific to that system and should not be run on another machine.
