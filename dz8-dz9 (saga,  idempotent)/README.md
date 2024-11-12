<h1>SAGA</h1>

![saga drawio](https://github.com/user-attachments/assets/19bcc8cc-e790-4b5e-9821-7820632d8b0d)

<h2>Компоненты</h2>

![saga](https://github.com/user-attachments/assets/e8543c8f-ee73-403d-82f3-dcc33e7bdf86)

<h2>Установка</h2>

<body>
<code>helm upgrade --install order helm/order -n saga
helm upgrade --install storage helm\storage -n saga
helm upgrade --install delivery helm\delivery -n saga
helm upgrade --install payment helm\payment -n saga<code/><body/>