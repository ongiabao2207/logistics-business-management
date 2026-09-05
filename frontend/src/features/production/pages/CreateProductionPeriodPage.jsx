import { useNavigate } from "react-router-dom";

import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { CreateProductionPeriodModal } from "../components/CreateProductionPeriodModal.jsx";
import "../styles/production.css";

export function CreateProductionPeriodPage() {
  usePageTitle("Khai báo kỳ sản lượng");
  const navigate = useNavigate();

  return (
    <CreateProductionPeriodModal
      isOpen
      pageMode
      onClose={() => navigate("/production")}
      onSuccess={() => navigate("/production")}
    />
  );
}
