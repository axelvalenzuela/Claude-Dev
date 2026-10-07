import { util } from "@aws-appsync/utils";

export function request(ctx) {
  const item = {
    ...ctx.args.input,
    createdAt: util.time.nowISO8601(),
  };
  return {
    operation: "PutItem",
    key: util.dynamodb.toMapValues({ owner: ctx.identity.sub, id: util.autoId() }),
    attributeValues: util.dynamodb.toMapValues(item),
    condition: { expression: "attribute_not_exists(id)" },
  };
}

export function response(ctx) {
  if (ctx.error) {
    util.error(ctx.error.message, ctx.error.type);
  }
  return ctx.result;
}
