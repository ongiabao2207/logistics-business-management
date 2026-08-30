import { DataState } from "../../../shared/components/DataState.jsx";
import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";

export function NotificationListPage() {
  usePageTitle("Notifications");

  return (
    <>
      <PageHeader
        eyebrow="Notification Service"
        title="Notifications"
        description="View user notifications created from asynchronous business events."
      />
      <DataState
        title="Notification module placeholder"
        description="Notification Service is planned as a RabbitMQ consumer and can be connected later through its public API."
      />
    </>
  );
}
