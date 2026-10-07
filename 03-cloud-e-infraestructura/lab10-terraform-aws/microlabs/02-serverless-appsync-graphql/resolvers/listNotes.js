import { util } from "@aws-appsync/utils";

export function request(ctx) {
  return {
    operation: "Query",
    query: {
      expression: "#owner = :owner",
      expressionNames: { "#owner": "owner" },
      expressionValues: util.dynamodb.toMapValues({ ":owner": ctx.identity.sub }),
    },
    limit: Math.min(ctx.args.limit ?? 20, 100),
    nextToken: ctx.args.nextToken,
  };
}

export function response(ctx) {
  if (ctx.error) {
    util.error(ctx.error.message, ctx.error.type);
  }
  return { items: ctx.result.items, nextToken: ctx.result.nextToken };
}
