import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import { DataState } from "../../../shared/components/DataState.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
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

function matchesDateRange(contract, from, to) {
  const validFrom = new Date(contract.valid_from).getTime();
  const validTo = new Date(contract.valid_to).getTime();
  const rangeFrom = from ? new Date(from).getTime() : null;
  const rangeTo = to ? new Date(to).getTime() : null;

  if (rangeFrom && validTo < rangeFrom) {
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

  const [filters, setFilters] = useState(initialFilters);
  const [page, setPage] = useState(1);
  const [selectedContractId, setSelectedContractId] = useState(null);
  const { data, isLoading, isError, error } = useContracts();
  const contracts = useMemo(() => (Array.isArray(data) ? data : []), [data]);

  const customerOptions = useMemo(
    () =>
      Array.from(new Set(contracts.map((contract) => contract.customer_name))).sort(
        (left, right) => left.localeCompare(right),
      ),
    [contracts],
  );

  const filteredContracts = useMemo(
    () => filterContracts(contracts, filters),
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
          <p>BizManage / Quản lý hợp đồng</p>
          <h1>Quản lý hợp đồng</h1>
        </div>
        <button className="button contract-create-button" type="button" disabled>
          <Plus size={18} />
          Lập hợp đồng mới
        </button>
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
