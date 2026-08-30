import { RouterProvider } from "react-router-dom";

import { AppProviders } from "./providers.jsx";
import { router } from "./router.jsx";

export function App() {
  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  );
}
