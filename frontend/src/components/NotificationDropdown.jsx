import { useState, useRef, useEffect } from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

function NotificationDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    deleteNotification
  } = useNotifications();

  // Fecha dropdown quando clica fora
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return 'checkmark-circle';
      case 'error':
        return 'alert-circle';
      case 'warning':
        return 'warning';
      default:
        return 'information-circle';
    }
  };

  const getNotificationColor = (type) => {
    switch (type) {
      case 'success':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      case 'warning':
        return 'text-yellow-400';
      default:
        return 'text-blue-400';
    }
  };

  const formatNotificationDate = (date) => {
    return format(new Date(date), 'dd/MM HH:mm', { locale: ptBR });
  };

  const handleNotificationClick = async (notification) => {
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }
  };

  const handleMarkAllAsRead = async () => {
    await markAllAsRead();
  };

  const handleDeleteNotification = async (notificationId, event) => {
    event.stopPropagation();
    await deleteNotification(notificationId);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Botão de notificação */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative text-gray-300 hover:text-white transition-colors"
      >
        <ion-icon name="notifications-outline" size="large"></ion-icon>

        {/* Badge de contagem */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}

        {/* Indicador de conexão */}
        <span className={`absolute -bottom-1 -right-1 w-2 h-2 rounded-full ${
          isConnected ? 'bg-green-400' : 'bg-red-400'
        }`}></span>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-nvidia-gray rounded-lg shadow-xl border border-nvidia-lightGray z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-nvidia-lightGray flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <h3 className="text-white font-semibold">Notificações</h3>
              {unreadCount > 0 && (
                <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                  {unreadCount}
                </span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllAsRead}
                className="text-nvidia-green hover:text-green-400 text-sm"
              >
                Marcar todas como lidas
              </button>
            )}
          </div>

          {/* Lista de notificações */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-6 text-center text-gray-400">
                <ion-icon name="notifications-off-outline" class="text-3xl mb-2"></ion-icon>
                <p>Nenhuma notificação</p>
              </div>
            ) : (
              notifications.slice(0, 10).map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  className={`px-4 py-3 border-b border-nvidia-lightGray cursor-pointer hover:bg-nvidia-lightGray transition-colors ${
                    !notification.is_read ? 'bg-nvidia-lightGray bg-opacity-50' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    {/* Ícone da notificação */}
                    <div className={`flex-shrink-0 ${getNotificationColor(notification.type)}`}>
                      <ion-icon
                        name={getNotificationIcon(notification.type)}
                        class="text-lg"
                      ></ion-icon>
                    </div>

                    {/* Conteúdo */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className={`text-sm font-medium ${
                            notification.is_read ? 'text-gray-300' : 'text-white'
                          }`}>
                            {notification.title}
                          </h4>
                          <p className={`text-sm mt-1 ${
                            notification.is_read ? 'text-gray-400' : 'text-gray-300'
                          }`}>
                            {notification.message}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            {formatNotificationDate(notification.created_at)}
                          </p>
                        </div>

                        {/* Botão de deletar */}
                        <button
                          onClick={(e) => handleDeleteNotification(notification.id, e)}
                          className="text-gray-400 hover:text-red-400 ml-2"
                        >
                          <ion-icon name="close-outline" class="text-sm"></ion-icon>
                        </button>
                      </div>

                      {/* Indicador de não lida */}
                      {!notification.is_read && (
                        <div className="w-2 h-2 bg-nvidia-green rounded-full mt-2"></div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 10 && (
            <div className="px-4 py-3 border-t border-nvidia-lightGray text-center">
              <button className="text-nvidia-green hover:text-green-400 text-sm">
                Ver todas as notificações
              </button>
            </div>
          )}

          {/* Status da conexão */}
          <div className="px-4 py-2 bg-nvidia-lightGray text-xs text-gray-400 flex items-center justify-between">
            <span>Status da conexão:</span>
            <div className="flex items-center space-x-1">
              <span className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-400' : 'bg-red-400'
              }`}></span>
              <span>{isConnected ? 'Conectado' : 'Desconectado'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default NotificationDropdown;