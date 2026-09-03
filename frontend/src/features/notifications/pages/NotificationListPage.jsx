import { DataState } from "../../../shared/components/DataState.jsx";
import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { useNotifications } from "../hooks/useNotifications.js";

export function NotificationListPage() {
  usePageTitle("Notifications");
  const notifications = useNotifications();

  if (notifications.isLoading) {
    return <DataState title="Loading notifications" description="Retrieving your notifications." />;
  }

  if (notifications.isError) {
    return <DataState title="Notifications unavailable" description={notifications.error?.message ?? "Please sign in and try again."} />;
  }

  const data = notifications.data;

  return (
    <>
      <PageHeader
        eyebrow="Notification Service"
        title="Notifications"
        description="View user notifications created from asynchronous business events."
      />
      {!data?.items?.length ? (
        <DataState title="No notifications" description="New production-period notifications will appear here." />
      ) : (
        <section className="card-stack" aria-label="Notification list">
          <p>{data.unread_count} unread notification(s)</p>
          {data.items.map((notification) => (
            <article className="card" key={notification.id}>
              <h2>{notification.title}</h2>
              <p>{notification.content}</p>
              <small>{notification.is_read ? "Read" : "Unread"} · {new Date(notification.created_at).toLocaleString()}</small>
            </article>
          ))}
        </section>
      )}
    </>
  );
}
