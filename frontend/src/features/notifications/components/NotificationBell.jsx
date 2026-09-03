import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, Check, LoaderCircle } from "lucide-react";

import { notificationApi } from "../api/notificationApi.js";
import { useNotifications } from "../hooks/useNotifications.js";
import "../styles/notifications.css";

function formatDate(value) {
  return new Date(value).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef(null);
  const queryClient = useQueryClient();
  const notifications = useNotifications();
  const data = notifications.data;

  const markAsRead = useMutation({
    mutationFn: notificationApi.markAsRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  useEffect(() => {
    function closeOnOutsideClick(event) {
      if (rootRef.current && !rootRef.current.contains(event.target)) setIsOpen(false);
    }

    function closeOnEscape(event) {
      if (event.key === "Escape") setIsOpen(false);
    }

    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);

  function togglePopup() {
    setIsOpen((open) => !open);
    if (!isOpen) notifications.refetch();
  }

  return (
    <div className="notification-bell" ref={rootRef}>
      <button
        className="notification-bell-button"
        type="button"
        onClick={togglePopup}
        aria-label="Mở thông báo"
        aria-expanded={isOpen}
        aria-haspopup="dialog"
      >
        <Bell size={21} strokeWidth={2.1} />
        {data?.unread_count > 0 && <span className="notification-badge">{data.unread_count > 99 ? "99+" : data.unread_count}</span>}
      </button>

      {isOpen && (
        <section className="notification-popup" role="dialog" aria-label="Thông báo">
          <header className="notification-popup-header">
            <div>
              <h2>Thông báo</h2>
              <p>{data?.unread_count ? `${data.unread_count} thông báo chưa đọc` : "Bạn đã đọc tất cả thông báo"}</p>
            </div>
            <Bell size={20} aria-hidden="true" />
          </header>

          <div className="notification-popup-list">
            {notifications.isLoading && <div className="notification-popup-state"><LoaderCircle className="spin" size={19} /> Đang tải thông báo...</div>}
            {notifications.isError && <div className="notification-popup-state is-error">Chưa thể tải thông báo. Vui lòng thử lại.</div>}
            {!notifications.isLoading && !notifications.isError && !data?.items?.length && <div className="notification-popup-state">Bạn chưa có thông báo mới.</div>}
            {data?.items?.map((notification) => (
              <button
                key={notification.id}
                className={`notification-item${notification.is_read ? "" : " is-unread"}`}
                type="button"
                onClick={() => !notification.is_read && markAsRead.mutate(notification.id)}
                disabled={markAsRead.isPending}
              >
                <span className="notification-item-dot" aria-hidden="true" />
                <span className="notification-item-content">
                  <strong>{notification.title}</strong>
                  <span>{notification.content}</span>
                  <time dateTime={notification.created_at}>{formatDate(notification.created_at)}</time>
                </span>
                {!notification.is_read && <Check size={16} className="notification-read-icon" aria-label="Đánh dấu đã đọc" />}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
