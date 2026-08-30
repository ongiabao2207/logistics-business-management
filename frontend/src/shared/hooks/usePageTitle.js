import { useEffect } from "react";

export function usePageTitle(title) {
  useEffect(() => {
    document.title = `${title} | Logistics Business Management`;
  }, [title]);
}
