def test_with_client(client):
    response = client.get('/')
    assert response.status_code == 200


def test_closed_page(admin_client):
    response = admin_client.get('/only-for-users/')
    assert response.status_code == 200


# Добавляем фикстуру client:
def test_with_authenticated_client(client, django_user_model):
    user = django_user_model.objects.create(username='yanote_user')
    # Логиним пользователя в клиенте без указания пароля:
    client.force_login(user)
    response = client.get('/private/')
    assert response.status_code == 200
