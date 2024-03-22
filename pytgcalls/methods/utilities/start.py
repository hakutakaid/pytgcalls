import asyncio
import logging

from ntgcalls import ConnectionNotFound
from ntgcalls import MediaState
from ntgcalls import StreamType

from ...exceptions import PyTgCallsAlreadyRunning
from ...mtproto import BridgedClient
from ...pytgcalls_session import PyTgCallsSession
from ...scaffold import Scaffold
from ...types import ChatUpdate
from ...types import StreamAudioEnded
from ...types import StreamVideoEnded
from ...types import Update
from ...types import UpdatedGroupCallParticipant

py_logger = logging.getLogger('pytgcalls')


class Start(Scaffold):
    async def start(self):

        @self._app.on_update()
        async def update_handler(update: Update):
            chat_id = update.chat_id
            if isinstance(update, ChatUpdate):
                if update.status & ChatUpdate.LEFT_VOICE_CHAT:
                    await clear_call(chat_id)
            if isinstance(update, UpdatedGroupCallParticipant):
                participant = update.participant
                chat_peer = self._cache_user_peer.get(chat_id)
                if chat_peer:
                    is_self = BridgedClient.chat_id(
                        chat_peer,
                    ) == participant.user_id if chat_peer else False
                    if is_self:
                        if participant.left:
                            await clear_call(chat_id)
                        if chat_id in self._need_unmute and \
                                not participant.joined and \
                                not participant.left and \
                                not participant.muted_by_admin:
                            try:
                                await update_status(
                                    chat_id,
                                    self._binding.get_state(chat_id),
                                )
                            except ConnectionNotFound:
                                pass

                        if participant.muted_by_admin and not participant.left:
                            self._need_unmute.add(chat_id)
                        else:
                            self._need_unmute.discard(chat_id)
            await self.propagate(
                update,
                self,
            )

        async def clear_call(chat_id):
            try:
                await self._binding.stop(chat_id)
            except ConnectionNotFound:
                pass
            await clear_cache(chat_id)

        async def update_status(chat_id: int, state: MediaState):
            try:
                await self._app.set_call_status(
                    chat_id,
                    state.muted,
                    state.video_paused,
                    state.video_stopped,
                    self._cache_user_peer.get(chat_id),
                )
            except Exception as e:
                py_logger.debug(f'SetVideoCallStatus: {e}')

        async def stream_ended(chat_id: int, stream: StreamType):
            await self.propagate(
                StreamAudioEnded(
                    chat_id,
                ) if stream == stream.Audio else
                StreamVideoEnded(
                    chat_id,
                ),
                self,
            )

        async def clear_cache(chat_id: int):
            self._cache_user_peer.pop(chat_id)
            self._need_unmute.discard(chat_id)

        if not self._is_running:
            self._is_running = True
            self._env_checker.check_environment()
            if not self._app.is_connected:
                await self._app.start()

            self._my_id = await self._app.get_id()
            self._cache_local_peer = await self._app.resolve_peer(
                self._my_id,
            )
            if self._app.no_updates:
                py_logger.warning(
                    f'Using {self._app.package_name.capitalize()} '
                    'client in no_updates mode is not recommended. '
                    'This mode may cause unexpected behavior or '
                    'limitations.',
                )
            else:
                self._handle_mtproto()

            self._binding.on_stream_end(
                lambda chat_id, stream: asyncio.run_coroutine_threadsafe(
                    stream_ended(chat_id, stream),
                    self.loop,
                ),
            )
            self._binding.on_upgrade(
                lambda chat_id, state: asyncio.run_coroutine_threadsafe(
                    update_status(chat_id, state),
                    self.loop,
                ),
            )
            self._binding.on_disconnect(
                lambda chat_id: asyncio.run_coroutine_threadsafe(
                    clear_cache(chat_id),
                    self.loop,
                ),
            )
            await PyTgCallsSession().start()
        else:
            raise PyTgCallsAlreadyRunning()
