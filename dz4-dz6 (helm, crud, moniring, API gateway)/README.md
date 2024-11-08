<img width="700" alt="flask" src="https://github.com/user-attachments/assets/8d66702a-6ae6-4d25-989f-0ec0890c9065">
<h3>Установка</h3>
<h4>CRUD</h4>
<body>
<code>helm upgrade --install crud-api-dz4 helm\crud-api-dz4</code>
<body/>

<h4>Ingress</h4>
<code>helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx/
helm install nginx ingress-nginx/ingress-nginx --namespace m -f values.yaml
</code>

<h4>Oauth2-proxy</h4>
<code>helm repo add oauth2-proxy https://oauth2-proxy.github.io/manifests
helm upgrade --install oauth2-proxy oauth2-proxy/oauth2-proxy --version 7.7.19 --namespace kk -f helm\oauth2-proxy\values.yaml
</code>

<h4>Keycloak</h4>
<code>helm repo add bitnami https://charts.bitnami.com/bitnami
helm upgrade -install keycloak bitnami/keycloak --version 22.2.4 --namespace kk -f helm\keycloak\values.yaml
</code>

<h4>PostgreSQL</h4>
<code>helm upgrade --install crud-db-postgresql -f helm\pg\values.yaml oci://registry-1.docker.io/bitnamicharts/postgresql</code>

<h4>Grafana</h4>
<code>helm repo add grafana https://grafana.github.io/helm-charts
helm upgrade --install grafana grafana/grafana --namespace pm -f C:\Users\zakar\Documents\arch-dz\dz4-dz5\helm\grafana\values.yaml --set-file dashboards.default.nginx.json=ingress.json --set-file dashboards.default.pg.json=pg.json --set-file dashboards.default.flask.json=flask.json --set-file dashboards.default.kube.json=kube.json
</code>
<h4>Prometheus</h4>
<code>helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install prometheus prometheus-community/prometheus --version 25.26.0 ‐‐namespace pm -f helm\prometheus\values.yaml
</code>
<h3>Dashboards
<h4>Flask</h4>
<img width="900" alt="flask" src="https://github.com/user-attachments/assets/4a59cbf3-e0b6-4774-8a96-25d87bc4aae2">
<h4>Ingress</h4>
<img width="900" alt="ingress" src="https://github.com/user-attachments/assets/a4b0637f-29ce-44ca-83f0-e48ade4588bd">
<h4>Kubernetes</h4>
<img width="900" alt="kube" src="https://github.com/user-attachments/assets/1cca2766-12b0-484e-93d4-ad89eb19940d">
<img width="900" alt="kube2" src="https://github.com/user-attachments/assets/bbadaa06-2b78-4e9d-b335-ca720e103025">
<h4>PostgreSQL</h4>
<img width="900" alt="pg" src="https://github.com/user-attachments/assets/42cb7172-93ab-4519-9708-ac3c4d09117b">
<img width="900" alt="pg2" src="https://github.com/user-attachments/assets/6f62d077-c4d6-4f8e-a765-bdbcfc751bb7">