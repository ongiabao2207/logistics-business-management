import { useMemo, useState } from "react";
import { Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { DataState } from "../../../shared/components/DataState.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { ROLES } from "../../identity/constants/permissions";
import { useAuth } from "../../identity/hooks/useAuth";
import { ContractDetailModal } from "../components/ContractDetailModal.jsx";
import { ContractFilters } from "../components/ContractFilters.jsx";
import { ContractKpiCards } from "../components/ContractKpiCards.jsx";
import { ContractPagination } from "../components/ContractPagination.jsx";
import { ContractTable } from "../components/ContractTable.jsx";
import { useContracts } from "../hooks/useContracts";
import "../contracts.css";

const PAGE_SIZE = 5;

const initialFilters = {
  search: "",
  customer: "",
  from: "",
  to: "",
  status: "",
};

function parseFilterDate(value) {
  const trimmedValue = value.trim();
  const ddMmYyyyMatch = trimmedValue.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);

  if (ddMmYyyyMatch) {
    const [, day, month, year] = ddMmYyyyMatch;
    const date = new Date(Number(year), Number(month) - 1, Number(day));

    if (
      date.getFullYear() === Number(year) &&
      date.getMonth() === Number(month) - 1 &&
      date.getDate() === Number(day)
    ) {
      return date.getTime();
    }

    return null;
  }

  const isoMatch = trimmedValue.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoMatch) {
    return new Date(trimmedValue).getTime();
  }

  return null;
}

function matchesDateRange(contract, from, to) {
  const validFrom = new Date(contract.valid_from).getTime();
  const rangeFrom = from ? parseFilterDate(from) : null;
  const rangeTo = to ? parseFilterDate(to) : null;

  if (from && rangeFrom === null) {
    return true;
  }

  if (to && rangeTo === null) {
    return true;
  }

  if (rangeFrom && validFrom < rangeFrom) {
    return false;
  }

  if (rangeTo && validFrom > rangeTo) {
    return false;
  }

  return true;
}

function filterContracts(contracts, filters) {
  const search = filters.search.trim().toLowerCase();

  return contracts.filter((contract) => {
    const matchesSearch =
      !search ||
      contract.contract_id.toLowerCase().includes(search) ||
      contract.customer_name.toLowerCase().includes(search);
    const matchesCustomer =
      !filters.customer || contract.customer_name === filters.customer;
    const matchesStatus = !filters.status || contract.status === filters.status;

    return (
      matchesSearch &&
      matchesCustomer &&
      matchesStatus &&
      matchesDateRange(contract, filters.from, filters.to)
    );
  });
}

export function ContractListPage() {
  usePageTitle("Contracts");

  const { user } = useAuth();
  const navigate = useNavigate();
  const [filters, setFilters] = useState(initialFilters);
  const [page, setPage] = useState(1);
  const [selectedContractId, setSelectedContractId] = useState(null);
  const { data, isLoading, isError, error } = useContracts();
  const contracts = useMemo(() => (Array.isArray(data) ? data : []), [data]);
  const canCreateContract = user?.role === ROLES.SALE;

  const customerOptions = useMemo(
    () =>
      Array.from(new Set(contracts.map((contract) => contract.customer_name))).sort(
        (left, right) => left.localeCompare(right),
      ),
    [contracts],
  );

  const filteredContracts = useMemo(
    () =>
      filterContracts(contracts, filters).toSorted((left, right) =>
        left.contract_id.localeCompare(right.contract_id, undefined, {
          numeric: true,
          sensitivity: "base",
        }),
      ),
    [contracts, filters],
  );
  const totalPages = Math.max(1, Math.ceil(filteredContracts.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const pagedContracts = filteredContracts.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  function updateFilters(nextFilters) {
    setFilters((currentFilters) => ({ ...currentFilters, ...nextFilters }));
    setPage(1);
  }

  return (
    <div className="contract-page">
      <div className="contract-page-heading">
        <div>
          <p>Contract Service / Quản lý hợp đồng</p>
          <h1>Danh sách hợp đồng</h1>
        </div>
        {canCreateContract ? (
          <button
            className="button contract-create-button"
            type="button"
            onClick={() => navigate("/contracts/new")}
          >
            <Plus size={18} />
            Lập hợp đồng mới
          </button>
        ) : null}
      </div>

      <ContractFilters
        customers={customerOptions}
        filters={filters}
        onChange={updateFilters}
      />

      {isLoading ? <DataState title="Đang tải danh sách hợp đồng" /> : null}
      {isError ? (
        <DataState
          title="Không tải được danh sách hợp đồng"
          description={error?.message ?? "Vui lòng thử lại sau."}
        />
      ) : null}
      {!isLoading && !isError && filteredContracts.length === 0 ? (
        <DataState
          title="Không có hợp đồng phù hợp"
          description="Thử điều chỉnh điều kiện tìm kiếm hoặc bộ lọc."
        />
      ) : null}
      {!isLoading && !isError && filteredContracts.length > 0 ? (
        <>
          <div className="contract-records">
            <ContractTable
              contracts={pagedContracts}
              onSelectContract={setSelectedContractId}
            />
            <ContractPagination
              page={currentPage}
              pageSize={PAGE_SIZE}
              totalItems={filteredContracts.length}
              onPageChange={setPage}
            />
          </div>
          <ContractKpiCards contracts={contracts} />
        </>
      ) : null}

      {selectedContractId ? (
        <ContractDetailModal
          contractId={selectedContractId}
          onClose={() => setSelectedContractId(null)}
        />
      ) : null}
    </div>
  );
}
