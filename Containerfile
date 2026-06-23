FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bootconfig.py .

# CGI server expects scripts in cgi-bin/
RUN mkdir cgi-bin && ln -s /app/bootconfig.py cgi-bin/bootconfig.py

# Default config — override by mounting your own bootconfig.yaml
COPY bootconfig.yaml.example bootconfig.yaml

# 8080 → iPXE bootscript (CGI)
EXPOSE 8080

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
