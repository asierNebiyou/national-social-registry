# National Social Registry — Celery image (workers + beat).
#
# Thin extension of the registry-platform celery base image (see
# docker/staff-api/Dockerfile for the full rationale). Adds only the NSR domain
# model; both celery packages, the run_celery.py wrapper, the CELERY_* ENV
# defaults and the CMD are inherited from the base. A single image runs as
# worker or beat, selected at runtime via CELERY_APP.
#
# Build context = repo root (so nsr-extension/ is reachable).
ARG RP_VERSION=1.2.2-rc.557
FROM openg2p/openg2p-registry-celery:${RP_VERSION}

# Option C: select NSR's domain model (coexists with the base image's reference
# extension; env picks NSR, no uninstall needed).
ENV REGISTRY_EXTENSION_MODULE=openg2p_registry_nsr_extension

COPY nsr-extension/ /app/nsr-extension/
RUN pip install --no-cache-dir /app/nsr-extension
