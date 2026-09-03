import { useCallback, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { useContracts } from "../../contracts/hooks/useContracts.js";
import { paymentCustomerApi } from "../api/paymentCustomerApi.js";

export function usePaymentContracts() {
  const contractsQuery = useContracts();
  const customersQuery = useQuery({
    queryKey: ["payment-customers"],
    queryFn: paymentCustomerApi.listCustomers,
  });
  const refetchContracts = contractsQuery.refetch;
  const refetchCustomers = customersQuery.refetch;

  const contracts = useMemo(
    () => contractsQuery.data ?? [],
    [contractsQuery.data],
  );
  const customers = useMemo(
    () => customersQuery.data ?? [],
    [customersQuery.data],
  );

  const contractById = useMemo(
    () => new Map(contracts.map((contract) => [contract.contract_id, contract])),
    [contracts],
  );

  const customerById = useMemo(
    () => new Map(customers.map((customer) => [customer.id, customer])),
    [customers],
  );

  const customerIdByName = useMemo(
    () => new Map(customers.map((customer) => [customer.company_name, customer.id])),
    [customers],
  );

  const getCustomerName = useCallback((contractId, customerId) => {
    return (
      customerById.get(customerId)?.company_name ??
      contractById.get(contractId)?.customer_name ??
      customerId ??
      "Chưa xác định"
    );
  }, [contractById, customerById]);

  const getCustomerId = useCallback((contract) => (
    contract.customer_id ?? customerIdByName.get(contract.customer_name)
  ), [customerIdByName]);

  const refetch = useCallback(async () => {
    const [contractResult, customerResult] = await Promise.all([
      refetchContracts(),
      refetchCustomers(),
    ]);
    return {
      data: contractResult.data,
      isError: contractResult.isError || customerResult.isError,
    };
  }, [refetchContracts, refetchCustomers]);

  return {
    ...contractsQuery,
    contracts,
    contractById,
    customers,
    customerById,
    error: contractsQuery.error ?? customersQuery.error,
    getCustomerId,
    getCustomerName,
    isPending: contractsQuery.isPending || customersQuery.isPending,
    refetch,
  };
}
