import { useMemo } from "react";

import { fakeCustomers } from "../../contracts/data/fakeCustomers.js";
import { useContracts } from "../../contracts/hooks/useContracts.js";

export function usePaymentContracts() {
  const query = useContracts();
  const contracts = useMemo(() => query.data ?? [], [query.data]);

  const contractById = useMemo(
    () => new Map(contracts.map((contract) => [contract.contract_id, contract])),
    [contracts],
  );

  const customerById = useMemo(
    () => new Map(fakeCustomers.map((customer) => [customer.id, customer])),
    [],
  );

  function getCustomerName(contractId, customerId) {
    return (
      contractById.get(contractId)?.customer_name ??
      customerById.get(customerId)?.name ??
      customerId ??
      "Chưa xác định"
    );
  }

  function getCustomerId(contract) {
    return fakeCustomers.find(
      (customer) => customer.name === contract.customer_name,
    )?.id;
  }

  return {
    ...query,
    contracts,
    contractById,
    getCustomerId,
    getCustomerName,
  };
}
