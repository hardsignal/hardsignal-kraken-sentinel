from copy import deepcopy

from watcher.tracker_policy import TRACK_WINDOW


class SourceEpisodeEngine:
    def __init__(self):
        self.next_episode_id = 1
        self.active_episode = None
        self.completed_episodes = []

    def _is_established_track(self, tracker_result):
        return (
            tracker_result["track_state"] == "TRACK_STABLE"
            and tracker_result["track_mean"] is not None
            and tracker_result["track_support"] >= TRACK_WINDOW
            and tracker_result["track_health"] != "LOST"
        )

    def _open_episode(self, observation_index, tracker_result):
        episode = {
            "episode_id": self.next_episode_id,
            "status": "ACTIVE",
            "start_index": observation_index,
            "end_index": None,
            "end_reason": None,
            "start_mean": tracker_result["track_mean"],
            "latest_mean": tracker_result["track_mean"],
            "max_support": tracker_result["track_support"],
            "degraded_seen": (
                tracker_result["track_health"] == "DEGRADED"
            ),
        }

        self.next_episode_id += 1
        self.active_episode = episode

        return {
            "event": "EPISODE_STARTED",
            "episode_id": episode["episode_id"],
            "observation_index": observation_index,
        }

    def _close_episode(self, observation_index, reason):
        episode = self.active_episode

        episode["status"] = "CLOSED"
        episode["end_index"] = observation_index
        episode["end_reason"] = reason

        self.completed_episodes.append(deepcopy(episode))
        self.active_episode = None

        return {
            "event": "EPISODE_CLOSED",
            "episode_id": episode["episode_id"],
            "observation_index": observation_index,
            "reason": reason,
        }

    def process(self, observation_index, tracker_result):
        events = []

        established = self._is_established_track(tracker_result)

        # A confirmed clean shift is a hard episode boundary.
        # The confirmation observation belongs to the new episode.
        if tracker_result["shift_confirmed"]:
            if self.active_episode is not None:
                events.append(
                    self._close_episode(
                        observation_index - 1,
                        "SHIFT_CONFIRMED",
                    )
                )

            if established:
                events.append(
                    self._open_episode(
                        observation_index,
                        tracker_result,
                    )
                )

        # Loss closes the active episode.
        elif tracker_result["track_health"] == "LOST":
            if self.active_episode is not None:
                events.append(
                    self._close_episode(
                        observation_index,
                        "TRACK_LOST",
                    )
                )

        # First established track starts an episode.
        elif self.active_episode is None:
            if established:
                events.append(
                    self._open_episode(
                        observation_index,
                        tracker_result,
                    )
                )

        # Normal continuation of the current source episode.
        else:
            if (
                tracker_result["track_state"] == "TRACK_STABLE"
                and tracker_result["track_mean"] is not None
            ):
                self.active_episode["latest_mean"] = (
                    tracker_result["track_mean"]
                )

            self.active_episode["max_support"] = max(
                self.active_episode["max_support"],
                tracker_result["track_support"],
            )

            if tracker_result["track_health"] == "DEGRADED":
                self.active_episode["degraded_seen"] = True

        return {
            "events": events,
            "active_episode": (
                None
                if self.active_episode is None
                else deepcopy(self.active_episode)
            ),
            "completed_count": len(self.completed_episodes),
        }
