import React, { createContext, useContext, useEffect, useState } from "react";
import api from "../services/api";

const HealthContext = createContext({ health: null, loading: true, error: null });

export function HealthProvider({ children }) {
  const [state, setState] = useState({ health: null, loading: true, error: null });

  useEffect(() => {
    let alive = true;
    api
      .health()
      .then((health) => alive && setState({ health, loading: false, error: null }))
      .catch((error) =>
        alive && setState({ health: null, loading: false, error: error.message })
      );
    return () => {
      alive = false;
    };
  }, []);

  return <HealthContext.Provider value={state}>{children}</HealthContext.Provider>;
}

export function useHealth() {
  return useContext(HealthContext);
}
