# Bem-vindo ao **TRAVELY**

## O Travely é um website desenvolvido em Python que permite aos usuários agendarem e organizarem suas viagens, conhecendo a história local e a cultura do país. Nele há sistemas de busca, agendamento, e-mails de avisos, perfil de usuário, sistema de avaliações e utilizando uma API do Google Calendar. O projeto teve como objetivo o TCC do curso de Desenvolvimento de Sistemas pela ETEC, sendo um website voltado para o turismo. Para funcionar corretamente seria necessário adicionar algumas informações no banco de dados, como turistas e guias, passeios, fotos e agendamentos. Nele ulizizamos:

```
Python
MySQL
Flask
Jinja2
Bootstrap
HTML
CSS
JavaScript (somente orentada à objetos)
API do Google Calendar
API do Amazon AWS S3 (S3)
```

## Sinta-se à vontade para fazer um Pull Request e contribuir com o projeto. Sabemos que o projeto há várias falhas, ele foi feito para fins de estudos, não tivemos muito tempo para realizar-lo, mas demos o nosso melhor! 


## **INSTALAÇÕES TRAVELY**

### Ativar o ambiente virtual
> python -m venv venv
> source venv/bin/activate  # No Windows: venv\Scripts\activate

### Instalar o Flask
> pip install Flask

### Instalar o Jinja2 (já incluído com Flask)
> pip install Jinja2

### Instalar o Bootstrap (via CDN)
### Para uso no HTML (não é necessário instalar via pip)
> <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
> <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

### Instalar o Bootstrap via npm
> npm install bootstrap

### Instalar a API do Google Calendar
> pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

### Instalar a biblioteca do AWS S3 (Boto3)
> pip install boto3
