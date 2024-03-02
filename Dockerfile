FROM python:3.9-slim

LABEL author="Blasteh <blasteh@blasteh.uk>"
RUN pip install prometheus_client requests pyyaml
COPY  app/givtcp_exporter.py /

CMD ["python", "-u", "/givtcp_exporter.py"]