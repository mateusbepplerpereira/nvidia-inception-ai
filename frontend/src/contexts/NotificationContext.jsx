import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { notificationsService } from '../services/api';

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [socket, setSocket] = useState(null);

  const loadNotifications = useCallback(async () => {
    try {
      const data = await notificationsService.getNotifications(50, 0);
      setNotifications(data);
    } catch (error) {
      console.error('Erro ao carregar notificações:', error);
    }
  }, []);

  const loadUnreadCount = useCallback(async () => {
    try {
      const data = await notificationsService.getUnreadCount();
      setUnreadCount(data.unread_count);
    } catch (error) {
      console.error('Erro ao carregar contagem não lidas:', error);
    }
  }, []);

  const connectWebSocket = useCallback(() => {
    if (socket) {
      socket.close();
    }

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/notifications/ws';
    const newSocket = new WebSocket(wsUrl);

    newSocket.onopen = () => {
      console.log('WebSocket conectado');
      setIsConnected(true);
    };

    newSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'notification') {
        // Verifica se a notificação já existe para evitar duplicatas
        setNotifications(prev => {
          const exists = prev.some(n => n.id === data.data.id);
          if (exists) {
            console.log(`Notificação ${data.data.id} já existe, ignorando duplicata`);
            return prev;
          }

          // Adiciona nova notificação apenas se não existir
          console.log(`Adicionando nova notificação via WebSocket: ${data.data.id}`);

          return [data.data, ...prev];
        });

        // Atualiza contador via API para ter valor correto
        loadUnreadCount();

        // Mostra notificação do navegador se permitido
        if (Notification.permission === 'granted') {
          new Notification(data.data.title, {
            body: data.data.message,
            icon: '/nvidia-icon.png', // Adicione um ícone se disponível
            tag: `notification-${data.data.id}`
          });
        }
      }
    };

    newSocket.onclose = () => {
      console.log('WebSocket desconectado');
      setIsConnected(false);

      // Reconecta automaticamente após 3 segundos
      setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };

    newSocket.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
      setIsConnected(false);
    };

    setSocket(newSocket);
  }, [socket, loadUnreadCount]);

  const markAsRead = useCallback(async (notificationId) => {
    try {
      await notificationsService.markAsRead(notificationId);

      // Atualiza estado local
      setNotifications(prev =>
        prev.map(notification =>
          notification.id === notificationId
            ? { ...notification, is_read: true }
            : notification
        )
      );

      // Decrementa contador se a notificação não estava lida
      const notification = notifications.find(n => n.id === notificationId);
      if (notification && !notification.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Erro ao marcar como lida:', error);
    }
  }, [notifications]);

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationsService.markAllAsRead();

      // Atualiza estado local
      setNotifications(prev =>
        prev.map(notification => ({ ...notification, is_read: true }))
      );
      setUnreadCount(0);
    } catch (error) {
      console.error('Erro ao marcar todas como lidas:', error);
    }
  }, []);

  const deleteNotification = useCallback(async (notificationId) => {
    try {
      await notificationsService.deleteNotification(notificationId);

      // Remove do estado local
      const notification = notifications.find(n => n.id === notificationId);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));

      // Decrementa contador se a notificação não estava lida
      if (notification && !notification.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Erro ao deletar notificação:', error);
    }
  }, [notifications]);

  // Solicita permissão para notificações do navegador
  const requestNotificationPermission = useCallback(async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      console.log('Permissão de notificação:', permission);
    }
  }, []);

  useEffect(() => {
    // Carrega dados iniciais
    loadNotifications();
    loadUnreadCount();

    // Solicita permissão para notificações
    requestNotificationPermission();

    // Conecta WebSocket
    connectWebSocket();

    // Cleanup
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  const value = {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    loadNotifications,
    loadUnreadCount
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};