<h1>SAGA</h1>

![saga drawio](https://github.com/user-attachments/assets/ddc5e423-5cb1-4893-b911-efd81e0c54d2)

<h2>Компоненты</h2>

![saga](https://github.com/user-attachments/assets/e8543c8f-ee73-403d-82f3-dcc33e7bdf86)

<h2>Установка</h2>

<body>
<code>helm upgrade --install order helm/order -n saga
helm upgrade --install storage helm\storage -n saga
helm upgrade --install delivery helm\delivery -n saga
helm upgrade --install payment helm\payment -n saga<code/><body/>