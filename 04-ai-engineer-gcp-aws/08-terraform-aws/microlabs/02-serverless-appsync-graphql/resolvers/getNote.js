import { util } from "@aws-appsync/utils";

// Solo el dueño puede leer su nota: la llave incluye el sub del JWT.
export function request(ctx) {
  return {
    operation: "GetItem",
    key: util.dynamodb.toMapValues({ owner: ctx.identity.sub, id: ctx.args.id }),
  };
}

export function response(ctx) {
  if (ctx.error) {
    util.error(ctx.error.message, ctx.error.type);
  }
  return ctx.result;
}
