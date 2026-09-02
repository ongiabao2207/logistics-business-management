import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { paymentApi } from "../api/paymentApi";

export const paymentKeys = {
  all: ["payments"],
  lists: () => [...paymentKeys.all, "list"],
  list: (params) => [...paymentKeys.lists(), params],
  detail: (id) => [...paymentKeys.all, "detail", id],
};

export function usePayments(params = { offset: 0, limit: 200 }) {
  return useQuery({
    queryKey: paymentKeys.list(params),
    queryFn: () => paymentApi.listPayments(params),
  });
}

export function usePayment(id) {
  return useQuery({ queryKey: paymentKeys.detail(id), queryFn: () => paymentApi.getPayment(id), enabled: Boolean(id) });
}

function usePaymentMutation(mutationFn) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess(payment) {
      queryClient.setQueryData(paymentKeys.detail(payment.id), payment);
      queryClient.invalidateQueries({ queryKey: paymentKeys.lists() });
    },
  });
}

export function usePreviewPayment() { return useMutation({ mutationFn: paymentApi.previewPayment }); }
export function useCreatePayment() { return usePaymentMutation(paymentApi.createPayment); }
export function useUpdatePayment() { return usePaymentMutation(({ id, payload }) => paymentApi.updatePayment(id, payload)); }
export function useSubmitPayment() { return usePaymentMutation(paymentApi.submitPayment); }
export function useCreateAdjustment() { return usePaymentMutation(({ id, payload }) => paymentApi.createAdjustment(id, payload)); }
