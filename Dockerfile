FROM python:3.12-alpine

LABEL maintainer="ylongwang2782"
LABEL description="BWG Stock Monitor - CN2 GIA-E stock monitoring with Telegram/Bark notifications"

WORKDIR /app

# Create non-root user for security
RUN adduser -D -u 1000 monitor

# Copy application
COPY --chown=monitor:monitor monitor.py .

# Create data directory for state file
RUN mkdir -p /app/data && chown monitor:monitor /app/data

USER monitor

# Environment variables with defaults
ENV CHECK_INTERVAL=180
ENV DAILY_REPORT_HOUR=12
ENV DATA_DIR=/app/data
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "python.*monitor.py" || exit 1

ENTRYPOINT ["python3", "monitor.py", "--daemon"]
