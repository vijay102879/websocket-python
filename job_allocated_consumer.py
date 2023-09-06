import json
import logging
from uuid import UUID
from app.core.redis import REDIS
from app.exceptions.operator_service_exceptions import OperatorServiceException
from app.tasks.consumers.base_consumer import BaseKafkaConsumer

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class JobAllocatedConsumer(BaseKafkaConsumer):
    async def on_message(self, message):
        try:
            data = json.loads(message.value.decode("utf-8"))
            logger.info(f"Received operator allocated request: {data}")

            payload = data.get('payload')
            operator_id = str(payload.get('operator_id'))
            desk_id = str(payload.get('desk_id'))

            locked_by_desk = await REDIS.client.hget("OPERATOR_LOCK", operator_id)
            websocket_message = json.dumps({"desk_id": desk_id, "operator_id": operator_id})
            await websocket_manager.broadcast_to_room('123', websocket_message)

            if locked_by_desk and locked_by_desk.decode() == desk_id:
                # Remove the operator from the lock list
                await REDIS.client.hdel("OPERATOR_LOCK", operator_id)

                await REDIS.client.zrem(f"DESK_QUEUE_{desk_id}", operator_id)
                return {"desk_id": desk_id, "operator_id": operator_id}
            else:
                pass

            logger.info(
                f"Operator removed from Redis with operator_id : {operator_id}"
            )
        except Exception as e:
            logger.error(e)

